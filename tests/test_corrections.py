import os
import shutil

import cv2 as cv
import numpy as np
import pandas as pd
import pytest
import tifffile as tf
from PIL import Image

import imgcorrect
import imgcorrect.zenith_co as zenith_co
from imgcorrect.corrections import take_closest_image
from imgcorrect.dataset import multispectral_ils_check
from imgcorrect.detect_panel import extract_panel_bounds

EXIFTOOL_PATH = (
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "exiftool",
        "exiftool.exe",
    )
    if os.name == "nt"
    else "exiftool"
)


@pytest.mark.parametrize("marker_id", [23, 63, 217, 220])
def test_aruco_marker_detection(marker_id):
    """Test that all four supported aruco marker IDs (23, 63, 217, 220) can be detected."""
    image = np.asarray(Image.open(f"tests/aruco_markers/aruco_{marker_id}.png")).astype(
        np.uint8
    )
    panel = extract_panel_bounds(image)

    assert panel is not None
    assert panel.aruco_id == marker_id


def test_aruco_no_marker():
    assert extract_panel_bounds(np.zeros((100, 100), dtype=np.uint8)) is None


def test_aruco_unsupported_marker():
    dictionary = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_6X6_250)
    marker = cv.aruco.generateImageMarker(dictionary, 99, 100)
    image = np.pad(marker, 20, constant_values=255)

    assert extract_panel_bounds(image) is None


@pytest.mark.parametrize("dtype", [np.float32, np.uint16])
def test_tiff_codec_round_trip(tmp_path, dtype):
    image = np.arange(100, dtype=dtype).reshape(10, 10)
    path = tmp_path / "corrected.tif"
    tf.imwrite(path, image, compression="deflate")

    restored = tf.imread(path)
    assert restored.dtype == image.dtype
    np.testing.assert_array_equal(restored, image)


def test_thermal_calibration_does_not_require_panel_reflectance():
    calibration_df = pd.DataFrame(
        {
            "band": ["lwir", "lwir", "red", "red"],
            "mean_reflectance": [np.nan, np.nan, 1000.0, 2000.0],
            "image_path": ["thermal1.tif", "thermal2.tif", "red1.tif", "red2.tif"],
        }
    )
    selected = calibration_df.groupby("band")[["mean_reflectance", "image_path"]].apply(
        take_closest_image
    )

    assert selected.loc["lwir", "image_path"] == "thermal1.tif"
    assert selected.loc["red", "image_path"] == "red2.tif"


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


def test_ms_ils_check():
    multispectral_ils_check(
        input_path=os.path.normpath("tests/6x_images/"),
        calibration_id="CAL",
        output_file_path=os.path.normpath("tests/output/ms_ils_check.json"),
    )


def test_6x_cal_ils():
    imgcorrect.correct_images(
        input_path=os.path.normpath("tests/6x_images/"),
        calibration_id="CAL",
        output_path=os.path.normpath("tests/output/6x_cal_ils/"),
        no_ils_correct=False,
        no_reflectance_correct=False,
        all_panels=False,
        delete_original=False,
        exiftool_path=EXIFTOOL_PATH,
        uint16_output=False,
    )


def test_6x_no_ils_no_cal_u16():
    imgcorrect.correct_images(
        input_path=os.path.normpath("tests/6x_images/"),
        calibration_id="CAL",
        output_path=os.path.normpath("tests/output/6x_no_ils_no_cal_u16/"),
        no_ils_correct=True,
        no_reflectance_correct=True,
        all_panels=False,
        delete_original=False,
        exiftool_path=EXIFTOOL_PATH,
        uint16_output=True,
    )


def test_6x_thermal_cal_ils():
    imgcorrect.correct_images(
        input_path=os.path.normpath("tests/6x_thermal_images/"),
        calibration_id="CAL",
        output_path=os.path.normpath("tests/output/6x_thermal_cal_ils/"),
        no_ils_correct=False,
        no_reflectance_correct=False,
        all_panels=False,
        delete_original=False,
        exiftool_path=EXIFTOOL_PATH,
        uint16_output=False,
    )


def test_6x_thermal_no_ils_no_cal_u16():
    imgcorrect.correct_images(
        input_path=os.path.normpath("tests/6x_thermal_images/"),
        calibration_id="CAL",
        output_path=os.path.normpath("tests/output/6x_thermal_no_ils_no_cal_u16/"),
        no_ils_correct=True,
        no_reflectance_correct=True,
        all_panels=False,
        delete_original=False,
        exiftool_path=EXIFTOOL_PATH,
        uint16_output=True,
    )


def test_d4k_no_ils_no_cal():
    imgcorrect.correct_images(
        input_path=os.path.normpath("tests/d4k_images/"),
        calibration_id="CAL",
        output_path=os.path.normpath("tests/output/d4k_no_ils_no_cal/"),
        no_ils_correct=True,
        no_reflectance_correct=True,
        all_panels=False,
        delete_original=False,
        exiftool_path=EXIFTOOL_PATH,
        uint16_output=False,
    )


def test_m3m_cal_ils():
    imgcorrect.correct_images(
        input_path=os.path.normpath("tests/m3m_images/"),
        calibration_id="CAL",
        output_path=os.path.normpath("tests/output/m3m_cal_ils/"),
        no_ils_correct=False,
        no_reflectance_correct=False,
        all_panels=False,
        delete_original=False,
        exiftool_path=EXIFTOOL_PATH,
        uint16_output=False,
    )


@pytest.fixture(scope="session", autouse=True)
def clean_up_outputs():
    yield
    shutil.rmtree(os.path.normpath("tests/output/"), ignore_errors=True)
