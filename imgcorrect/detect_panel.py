"""Aruco panel detection and reflectance calculation."""

import logging
from typing import NamedTuple, Tuple

import cv2 as cv
import numpy as np
from PIL import Image

# Constants
ARUCO_SIDE_LENGTH_M = 0.07
ARUCO_TOP_TO_PANEL_CENTER_M = 0.06

SAMPLE_RECT_HEIGHT = 0.04
SAMPLE_RECT_WIDTH = 0.04

logger = logging.getLogger(__name__)


class BoundingBox(NamedTuple):
    """Lightweight class representing a non-rotated bounding box as a pair of top left and bottom right (X, Y) points."""

    top_left: Tuple[int, int]
    bottom_right: Tuple[int, int]
    aruco_id: int

    def bounds(self):
        """Return a sequence of slice objects that allow for use of the bounding box in NumPy indexing expressions."""
        return slice(self.top_left[1], self.bottom_right[1]), slice(
            self.top_left[0], self.bottom_right[0]
        )


def convert_to_type(image, max_val, desired_type=np.uint8):
    """
    Convert the data type of a numpy array to another data type, scaling accordingly.

    :param image: The array to convert
    :param max_val: The max_val of the input array
    :param desired_type: The desired type
    :return: The converted image in numpy.array format
    """
    image = image / max_val  # Scale to 0-1
    image = np.iinfo(desired_type).max * image  # Scale back to desired type
    return image.astype(desired_type)


def extract_panel_bounds(image):
    """
    Detect an Aruco marker attached to a reflectance calibration panel and calculates the location of the panel itself.

    It is important to note that the function relies on an orientation of the calibration panel in which:
    (1) The orientation of the Aruco marker is rotated 90 degrees clock-wise from the standard orientation,
    with its top left corner forming the top right of the marker in the image.
    (2) The reflectance panel itself is situated directly above the Aruco marker in the image.

    :param image: The NumPy array of the image
    :return: The non-rotated bounding box of the panel, as a BoundingBox object
    """
    # o------>  +X
    # |
    # |
    # v +Y
    dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_250)
    corners, ids, rejected_img_points = cv.aruco.detectMarkers(image, dictionary)

    # if at least one marker detected
    if ids is not None:
        aruco_side_length_p = cv.norm(corners[0][0][1] - corners[0][0][0])
        gsd = ARUCO_SIDE_LENGTH_M / aruco_side_length_p
        logger.debug("Calibration image GSD: %10.5f m/pixel", gsd)

        # by default, expects panel to left of aruco marker
        top_aruco_line = corners[0][0][0] - corners[0][0][3]
        top_aruco_line_middle = top_aruco_line / 2.0 + corners[0][0][3]

        # panels with markers of id:63 are incorrectly oriented
        # in this case, panel is beneath marker
        if ids[0][0] == 63:
            logger.info("Aruco ID: 63 detected. Adjusting for panel beneath marker.")
            top_aruco_line = corners[0][0][3] - corners[0][0][2]
            top_aruco_line_middle = top_aruco_line / 2.0 + corners[0][0][2]

        top_aruco_line_normal = np.array([top_aruco_line[1], -top_aruco_line[0]])

        top_aruco_line_normal /= cv.norm(top_aruco_line_normal)
        top_aruco_line_normal_scaled_pixels = (
            ARUCO_TOP_TO_PANEL_CENTER_M / gsd
        ) * top_aruco_line_normal

        sample_center = top_aruco_line_middle + top_aruco_line_normal_scaled_pixels
        sample_top_left_corner = np.array(
            [
                sample_center[0] - (SAMPLE_RECT_HEIGHT / 2.0) / gsd,
                sample_center[1] - (SAMPLE_RECT_WIDTH / 2.0) / gsd,
            ]
        )

        top_left = (int(sample_top_left_corner[0]), int(sample_top_left_corner[1]))
        bottom_right = (
            int(top_left[0] + SAMPLE_RECT_WIDTH / gsd),
            int(top_left[1] + SAMPLE_RECT_HEIGHT / gsd),
        )
        return BoundingBox(
            top_left=top_left, bottom_right=bottom_right, aruco_id=ids[0][0]
        )
    else:
        return None


def isolate_band(image, band_math_arr):
    """
    Isolate a single band by performing bandmath on a multi-channel image.

    :param image: The multi-channel image
    :param band_math_arr: Describes the band math required to isolate the desired band
    :return: The isolated band
    """
    red_ch, green_ch, blue_ch = cv.split(image)
    return (
        (band_math_arr[0] * red_ch if band_math_arr[0] != 0 else 0)
        + (band_math_arr[1] * green_ch if band_math_arr[1] != 0 else 0)
        + (band_math_arr[2] * blue_ch if band_math_arr[2] != 0 else 0)
    )


def get_reflectance(row):
    """
    Detect pixels in the reflectance panel and calculates the average reflectance value.

    :param image_path: The path to a calibration image
    :return: The average value of the reflectance panel a valid calibration image, NaN if image is invalid
    """
    if "band_math" not in row.index:
        image = np.asarray(Image.open(row["image_path"])).astype(np.uint16)
        # OpenCV aruco detection only accepts 8-bit data
        panel = extract_panel_bounds(convert_to_type(image, row.max_val, np.uint8))
    else:
        image = np.asarray(Image.open(row["image_path"])).astype(np.uint8)
        panel = extract_panel_bounds(image)
        # Change array type to float so saturated values can be ignored during reflectance calculation
        image = image.astype(np.float32)
        saturation_indices = image >= 255
        image[saturation_indices] = np.nan
        # perform band math
        image = isolate_band(image, row.band_math)

    if panel is None:
        logger.info("No reflectance panel found. Mean DN: NaN")
        return np.nan, np.nan
    else:
        reflectance_pixels = image[panel.bounds()]
        mean_reflectance_digital_number = reflectance_pixels.mean()

        logger.info("Mean DN: %10.5f", mean_reflectance_digital_number)
        return mean_reflectance_digital_number, panel.aruco_id
