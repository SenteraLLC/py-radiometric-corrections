import os

import cv2 as cv
import numpy as np
from PIL import Image

import imgcorrect
import imgcorrect.detect_panel as detect_panel
import imgcorrect.zenith_co as zenith_co


def test_aruco_marker_detection():
    """Test that all four supported aruco marker IDs (23, 63, 217, 220) can be detected."""
    dictionary = cv.aruco.Dictionary_get(cv.aruco.DICT_6X6_250)

    # Test all four marker IDs
    for marker_id in [23, 63, 217, 220]:
        test_image_path = f"tests/aruco_markers/aruco_{marker_id}.png"

        # Skip test if image doesn't exist
        if not os.path.exists(test_image_path):
            print(f"Skipping test: {test_image_path} not found")
            continue

        # Load the test image
        image = np.asarray(Image.open(test_image_path)).astype(np.uint8)

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image_gray = cv.cvtColor(image, cv.COLOR_RGB2GRAY)
        else:
            image_gray = image

        # Detect aruco markers
        corners, ids, rejected = cv.aruco.detectMarkers(image_gray, dictionary)

        # Verify the expected marker was detected
        assert ids is not None, f"No aruco markers detected in {test_image_path}"
        assert (
            marker_id in ids
        ), f"Aruco marker {marker_id} not detected. Found: {ids.flatten().tolist()}"
        print(f"Successfully detected aruco marker ID: {marker_id}")


def test_aruco_marker_coefficient_selection():
    """Test that each aruco marker ID maps to the correct coefficient array."""
    # Test that all four batch coefficients are properly loaded
    assert (
        len(zenith_co.sg3144_batch1_coefficients) > 250
    ), "Batch1 coefficients not loaded properly"
    assert (
        len(zenith_co.sg3144_batch2_coefficients) > 250
    ), "Batch2 coefficients not loaded properly"
    assert (
        len(zenith_co.sg3144_batch3_coefficients) > 250
    ), "Batch3 coefficients not loaded properly"
    assert (
        len(zenith_co.sg3144_batch4_coefficients) > 250
    ), "Batch4 coefficients not loaded properly"

    # Verify they are lists, not tuples (no trailing comma issue)
    assert isinstance(
        zenith_co.sg3144_batch1_coefficients, list
    ), "Batch1 should be a list"
    assert isinstance(
        zenith_co.sg3144_batch2_coefficients, list
    ), "Batch2 should be a list"
    assert isinstance(
        zenith_co.sg3144_batch3_coefficients, list
    ), "Batch3 should be a list"
    assert isinstance(
        zenith_co.sg3144_batch4_coefficients, list
    ), "Batch4 should be a list"

    # Verify the first few non-zero values match expected batch data
    # Batch1 at index 250 should be 0.1239909
    assert (
        abs(zenith_co.sg3144_batch1_coefficients[250] - 0.1239909) < 0.00001
    ), "Batch1 coefficient mismatch"

    # Batch2 at index 250 should be 0.13493395
    assert (
        abs(zenith_co.sg3144_batch2_coefficients[250] - 0.13493395) < 0.00001
    ), "Batch2 coefficient mismatch"

    # Batch3 at index 250 should be 0.11927114
    assert (
        abs(zenith_co.sg3144_batch3_coefficients[250] - 0.11927114) < 0.00001
    ), "Batch3 coefficient mismatch"

    # Batch4 at index 250 should be 0.12586513
    assert (
        abs(zenith_co.sg3144_batch4_coefficients[250] - 0.12586513) < 0.00001
    ), "Batch4 coefficient mismatch"

    # Verify all coefficients are numeric and non-negative
    for i, coeff in enumerate(zenith_co.sg3144_batch1_coefficients):
        assert isinstance(coeff, (int, float)), f"Batch1[{i}] is not numeric"
        assert coeff >= 0, f"Batch1[{i}] is negative"

    for i, coeff in enumerate(zenith_co.sg3144_batch2_coefficients):
        assert isinstance(coeff, (int, float)), f"Batch2[{i}] is not numeric"
        assert coeff >= 0, f"Batch2[{i}] is negative"

    for i, coeff in enumerate(zenith_co.sg3144_batch3_coefficients):
        assert isinstance(coeff, (int, float)), f"Batch3[{i}] is not numeric"
        assert coeff >= 0, f"Batch3[{i}] is negative"

    for i, coeff in enumerate(zenith_co.sg3144_batch4_coefficients):
        assert isinstance(coeff, (int, float)), f"Batch4[{i}] is not numeric"
        assert coeff >= 0, f"Batch4[{i}] is negative"


def test_6x_cal_ils():
    imgcorrect.correct_images(
        "tests/6x_images/",
        "CAL",
        "tests/output/6x_cal_ils/",
        False,
        False,
        False,
        False,
        "exiftool",
        False,
    )


def test_6x_cal_ils_u16():
    imgcorrect.correct_images(
        "tests/6x_images/",
        "CAL",
        "tests/output/6x_cal_ils_u16/",
        False,
        False,
        False,
        False,
        "exiftool",
        True,
    )


def test_6x_no_ils_no_cal_u16():
    imgcorrect.correct_images(
        "tests/6x_images/",
        "CAL",
        "tests/output/6x_no_ils_no_cal_u16/",
        True,
        True,
        False,
        False,
        "exiftool",
        True,
    )


def test_d4k_ils():
    imgcorrect.correct_images(
        "tests/d4k_images/",
        "CAL",
        "tests/output/d4k_ils/",
        False,
        True,
        False,
        False,
        "exiftool",
        False,
    )


def test_m3m_ils():
    imgcorrect.correct_images(
        "tests/m3m_images/",
        "CAL",
        "tests/output/m3m_ils/",
        False,
        False,
        False,
        False,
        "exiftool",
        False,
    )
