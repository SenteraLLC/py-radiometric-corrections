"""Radiometric corrections for Sentera sensors."""

import logging
import os
import tempfile

import imgparse
import numpy as np
import tifffile as tf
from PIL import Image
from tqdm import tqdm

from imgcorrect import detect_panel, io, metadata, thermal_convert, zenith_co

logger = logging.getLogger(__name__)

ROLLING_AVG_TIMESPAN = "3s"


def take_closest_image(df_grouped_by_band, target=2048):
    """Per band, return image with mean reflectance closest to target."""
    return df_grouped_by_band.iloc[
        (df_grouped_by_band.mean_reflectance - target).abs().argmin()
    ]


def compute_ils_correction(image_df):
    """Compute coefficient that will counteract incidental lighting variation."""

    def _rolling_avg(df):
        return df.astype(float).rolling(ROLLING_AVG_TIMESPAN, closed="both").mean()

    def _get_ils(row):
        return imgparse.get_ils(row.image_path)[0]

    try:
        image_df["ILS"] = image_df.apply(_get_ils, axis=1)
    except imgparse.ParsingError:
        raise Exception(
            "ILS data not found. Use --no-ils-correct flag to run corrections without ILS normalization."
        )

    image_df["timestamp"] = image_df.apply(
        lambda row: imgparse.get_timestamp(row.image_path, row.EXIF), axis=1
    )
    image_df = image_df.set_index("timestamp", drop=True).sort_index()

    image_df["averaged_ILS"] = image_df.groupby("band").ILS.transform(_rolling_avg)

    image_df["ILS_ratio"] = image_df.groupby("band").averaged_ILS.transform(
        lambda df: df / df.mean()
    )

    # NOTE: We keep the 'ILS' column here to use it to scale the reflectance correction later.
    return image_df.reset_index().drop(columns=["timestamp", "averaged_ILS"])


def compute_reflectance_correction(image_df, calibration_df, ils_present):
    """Compute coefficient that will scale output values to known panel reflectance."""

    def _get_band_coeff(row, coeffs):
        cent_arr, fwhm_arr = imgparse.get_wavelength_data(row.image_path)
        cent = int(cent_arr[int(row.XMP_index)])
        wfhm = int(fwhm_arr[int(row.XMP_index)])

        return np.average(coeffs[cent - wfhm : cent + wfhm + 1])

    def _get_ils_scaling(band_row):
        calibration_img_ils = imgparse.get_ils(band_row.image_path)[0]
        return band_row.ILS / calibration_img_ils

    if calibration_df.empty:
        raise FileNotFoundError(
            "No calibration images were found. If not attempting to correct for "
            "absolute reflectance, set the '--no_reflectance_correct' flag. Otherwise, "
            "set the calibration image identifier with the '--calibration_id' option."
        )

    # only calculate mean reflectance if it was not calculated previously to find calibration images
    calibration_df["mean_reflectance"] = calibration_df.apply(
        lambda row: detect_panel.get_reflectance(row)
        if row.cal_in_path
        else row.mean_reflectance,
        axis=1,
    )
    band_df = (
        calibration_df.groupby("band")[
            ["image_path", "mean_reflectance", "autoexposure", "XMP_index"]
        ]
        .apply(take_closest_image)
        .reset_index()
    )

    if ils_present:
        band_avg_ils = image_df.groupby("band").ILS.mean().reset_index()
        band_df["ils_scaling_factor"] = band_df.merge(band_avg_ils, on="band").apply(
            _get_ils_scaling, axis=1
        )
    else:
        band_df["ils_scaling_factor"] = 1

    band_df["slope_coefficient"] = (
        band_df.apply(
            lambda row: _get_band_coeff(row, zenith_co.zenith_coefficients), axis=1
        )
        / (band_df.mean_reflectance / band_df.autoexposure)
        * band_df.ils_scaling_factor
    )

    image_df = image_df.merge(
        band_df[["band", "slope_coefficient"]], on="band", how="outer"
    )
    if image_df["slope_coefficient"].isnull().values.any():
        raise FileNotFoundError(
            "Calibration imagery with a visible reference panel was not found for one or more bands."
        )

    return image_df


def compute_correction_coefficient(image_df_row):
    """Compute final correction coefficient."""
    return image_df_row.slope_coefficient / (
        image_df_row.autoexposure * image_df_row.ILS_ratio
    )


def adjust_scale(path, max_val, normalize, uint16_output):
    """Normalize and/or scale output values to 0-65535."""
    image_arr = np.asarray(Image.open(path)).astype(np.float32)
    if normalize:
        image_arr = image_arr / max_val
    if uint16_output:
        image_arr = image_arr * 65535
        image_arr = image_arr.astype(np.uint16)
    tf.imwrite(path, image_arr)


def apply_corrections(image_df_row):
    """Multiply input values by correction coefficients to generate reflectance values."""
    logger.debug("Applying correction to image: %s", image_df_row.image_path)

    image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
    # for images that represent data for multiple bands
    if "band_math" in image_df_row.index:
        # ignore saturated pixels
        saturation_indices = image_arr >= 255
        # ideally set to np.nan, but this messes up the stitching software
        image_arr[saturation_indices] = 255
        # perform band math
        image_arr = detect_panel.isolate_band(image_arr, image_df_row.band_math)

    image_arr = image_arr * image_df_row.correction_coefficient

    return image_arr


def correct_images(
    input_path,
    calibration_id,
    output_path,
    no_ils_correct,
    no_reflectance_correct,
    delete_original,
    exiftool_path,
    uint16_output,
):
    """
    Radiometrically correct images.

    For each image in the input_path directory (recursive), determine coefficients to correct for
    autoexposure and incidental lighting variance, and scale to mean reflectance of a calibration
    panel with known reflectance.
    """
    # Create new `pandas` methods which use `tqdm` progress
    # (can use tqdm_gui, optional kwargs, etc.)
    tqdm.pandas()

    logger.info("ILS corrections: %s", "Disabled" if no_ils_correct else "Enabled")
    logger.info("Delete original: %s", "Enabled" if delete_original else "Disabled")

    # Check for LWIR folder and convert images
    lwir_folder_path = None
    input_folders = [
        f for f in os.listdir(input_path) if os.path.isdir(os.path.join(input_path, f))
    ]
    if not input_folders:
        if "lwir" in os.path.split(input_path)[1].lower():
            lwir_folder_path = input_path
    for folder in input_folders:
        if "lwir" in folder.lower():
            lwir_folder_path = os.path.join(input_path, folder)

    if lwir_folder_path is not None:
        lwir_output_path = os.path.join(output_path, os.path.split(lwir_folder_path)[1])
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        thermal_convert.convert_thermal(
            lwir_folder_path, lwir_output_path, exiftool_path
        )

    # Read images:
    image_df = io.create_image_df(input_path, output_path)

    # Get image metadata:
    image_df["EXIF"] = image_df.image_path.apply(imgparse.get_exif_data)

    # Determine sensor type apply sensor specific settings
    image_df = io.apply_sensor_settings(image_df)

    # Get autoexposure correction:
    image_df["autoexposure"] = image_df.apply(
        lambda row: imgparse.get_autoexposure(row.image_path, row.EXIF), axis=1
    )

    # Split out calibration images, if present:
    if not no_reflectance_correct:
        calibration_df, image_df = io.create_cal_df(image_df, calibration_id)

    # Get ILS correction:
    if not no_ils_correct:
        image_df = compute_ils_correction(image_df)
    else:
        image_df["ILS_ratio"] = 1

    # Get reflectance correction:
    if not no_reflectance_correct:
        image_df = compute_reflectance_correction(
            image_df, calibration_df, not no_ils_correct
        )
    else:
        image_df["slope_coefficient"] = 1

    image_df["correction_coefficient"] = image_df.apply(
        lambda row: compute_correction_coefficient(row), axis=1
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        # Apply corrections:
        logger.info("Applying image corrections...")
        image_df = image_df.progress_apply(
            lambda row: io.write_image(apply_corrections(row), row, temp_dir), axis=1
        )

        # Adjust scale if necessary:
        if no_reflectance_correct or uint16_output:
            logger.info("Adjusting output scale...")
            image_df.temp_path.progress_apply(
                lambda path: adjust_scale(
                    path, image_df.max_val.max(), no_reflectance_correct, uint16_output
                )
            )

        # Copy EXIF:
        logger.info("Writing EXIF data...")
        # progress_apply is tqdm version of apply
        image_df.progress_apply(
            lambda row: metadata.copy_exif(row, exiftool_path), axis=1
        )

        # Delete input imagery if requested:
        if delete_original:
            io.delete_all_originals(image_df)

        # Move output imagery to correct output directory:
        io.move_corrected_images(image_df)
