import cv2 as cv
import numpy as np
import pandas as pd
import glob
from imgparse import imgparse

from PIL import Image

# Constants
MAX_VAL_12BIT = 4096

ARUCO_SIDE_LENGTH_M = 0.07
ARUCO_TOP_TO_PANEL_CENTER_M = 0.06

SAMPLE_RECT_HEIGHT = 0.04
SAMPLE_RECT_WIDTH = 0.04


def convert_to_type(image, desired_type=np.uint8):
    """
    Converts the 12-bit tiff from a 6X sensor to a numpy compatible form
    :param desired_type: The desired type
    :return: The converted image in numpy.array format
    """
    image = image / MAX_VAL_12BIT # Scale to 0-1
    image = np.iinfo(desired_type).max * image # Scale back to desired type
    return image.astype(desired_type)

def generate_aruco_marker(id=13):
    """
    Generates and writes to disk an aruco label
    :param id: The aruco id of a 6x6 block, 250x250 pixel dictionary, defaults 13
    :return: True/False
    """
    if (id >= 0 and id <=50):
        dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_250)
        cv.aruco.drawMarker(dictionary, id, 200, markerImage, 1)
        cv.imwrite("marker23.jpg", markerImage)
        return True
    else:
        return False


def extract_panel_bounds(image):
    """
    Extracts the top-left, bottom-right coordinates of a rectangular raster at the center 
    of the reflective panel 
    :param image: The numpy array of the image
    :return: list of an x,y tuple of top-left and bottom-right pixels
    """
    # o------>  +X
    # |
    # |
    # v +Y
    dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_250)
    
    corners, ids, rejectedImgPoints	= cv.aruco.detectMarkers(image, dictionary)
    # if at least one marker detected
    if (not ids is None):
        aruco_side_length_p = cv.norm(corners[0][0][1] - corners[0][0][0])
        gsd = ARUCO_SIDE_LENGTH_M / aruco_side_length_p
        print(f"GSD: {gsd:10.5f} m/pixel")

        top_aruco_line = corners[0][0][0] - corners[0][0][3]
        top_aruco_line_middle = top_aruco_line / 2.0 + corners[0][0][3]
        
        top_aruco_line_normal = np.array([top_aruco_line[1], -top_aruco_line[0]])

        top_aruco_line_normal /= cv.norm(top_aruco_line_normal)
        top_aruco_line_normal_scaled_pixels = (ARUCO_TOP_TO_PANEL_CENTER_M / gsd) * top_aruco_line_normal

        sample_center = top_aruco_line_middle + top_aruco_line_normal_scaled_pixels
        sample_top_left_corner = np.array([sample_center[0] - (SAMPLE_RECT_HEIGHT / 2.0) / gsd, sample_center[1] - (SAMPLE_RECT_WIDTH / 2.0) / gsd])

        top_left_x = int(sample_top_left_corner[0])
        top_left_y = int(sample_top_left_corner[1])
        bottom_right_x = top_left_x + int(sample_top_left_corner[0] + SAMPLE_RECT_WIDTH / gsd)
        bottom_right_y = top_left_y + int(sample_top_left_corner[1] + SAMPLE_RECT_HEIGHT / gsd)

        rectangle_position = [(top_left_x, top_left_y),
                              (bottom_right_x, bottom_right_y)]
        
        return rectangle_position      
    return None


def get_mean_reflectance_df(image_folder):
    """
    Detects pixels in the reflectance panel and decides on the best image to use for calibration
    :param image_folder: The path to the folder with the calibration images
    :return: A dataframe of the average values of the reflectance panel and the related autoexposure
             for every valid calibration image
    """
    df_object = pd.DataFrame(columns=['mean_reflectance', 'autoexposure'])
    image_files = glob.glob(image_folder + '/*.tif')
    for image_file in image_files:
        # Read the original (12-bit) tiff with the next largest commonly used container (16-bit)
        image_16bit = np.asarray(Image.open(image_file)).astype(np.uint16)
        # OpenCV aruco detection only accepts 8-bit data
        image_8bit = convert_to_type(image_16bit, np.uint8)
        rectangle_position = extract_panel_bounds(image_8bit)
        if rectangle_position is None:
            continue

        # Visualize the rectangle for verification purposes
        # image_copy = image_8bit.copy()
        # x_start = rectangle_position[0][0]
        # y_start = rectangle_position[0][1]
        # x_end = rectangle_position[1][0]
        # y_end = rectangle_position[1][1]
        # image_copy = cv.rectangle(image_copy,(x_start, y_start),(x_end, y_end),(0,255,0),3)
        # cv.imwrite("res"+str(np.random.rand())+".jpg", image_copy)

        reflectance_pixels = image_16bit[rectangle_position[0][0]:rectangle_position[1][0],
                                         rectangle_position[0][1]:rectangle_position[1][1]]
        mean_reflectance_digital_number = reflectance_pixels.mean()
        print(f"Mean DN: {mean_reflectance_digital_number:10.5}")

        df_object = df_object.append({'mean_reflectance': mean_reflectance_digital_number, 
                                      'autoexposure': imgparse.get_autoexposure(image_file)},
                                      ignore_index=True)

    return df_object
        