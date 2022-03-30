import imgparse
import logging

import cv2 as cv
import numpy as np
from PIL import Image
import tifffile as tf

from imgcorrect import detect_panel, io

logger = logging.getLogger(__name__)

ROLLING_AVG_TIMESPAN = '3s'

def take_closest_image(df_grouped_by_band, target=2048):
    return df_grouped_by_band.iloc[(df_grouped_by_band.mean_reflectance - target).abs().argmin()]


def compute_ils_correction(image_df):
    def _rolling_avg(df):
        return df.astype(float).rolling(ROLLING_AVG_TIMESPAN, closed='both').mean()

    def _get_ILS(row):
        return imgparse.get_ils(row.image_path)[0]

    try:
        image_df['ILS'] = image_df.apply(_get_ILS, axis=1)
    except:
        raise Exception("ILS data not found. Use --no-ils-correct flag to run corrections without ILS normalization.")

    image_df['timestamp'] = image_df.apply(lambda row: imgparse.get_timestamp(row.image_path, row.EXIF), axis=1)
    image_df = image_df.set_index('timestamp', drop=True).sort_index()

    image_df['averaged_ILS'] = image_df.groupby('band').ILS.transform(_rolling_avg)

    image_df['ILS_ratio'] = image_df.groupby('band').averaged_ILS.transform(lambda df: df / df.mean())

    # NOTE: We keep the 'ILS' column here to use it to scale the reflectance correction later.
    return image_df.reset_index().drop(columns=['timestamp', 'averaged_ILS'])


def compute_reflectance_correction(image_df, calibration_df, ils_present):
    def _get_band_coeff(row, coeffs):
        cent_arr, fwhm_arr = imgparse.get_wavelength_data(row.image_path)
        cent = int(cent_arr[int(row.XMP_index)])
        wfhm = int(fwhm_arr[int(row.XMP_index)])

        return np.average(coeffs[cent-wfhm:cent+wfhm+1])

    def _get_ils_scaling(band_row):
        calibration_img_ils = imgparse.get_ils(band_row.image_path)[0]
        return band_row.ILS / calibration_img_ils

    if calibration_df.empty:
        raise FileNotFoundError("No calibration images were found. If not attempting to correct for "
                                "absolute reflectance, set the '--no_reflectance_correct' flag. Otherwise, "
                                "set the calibration image identifier with the '--calibration_id' option.")

    # only calculate mean reflectance if it was not calculated previously to find calibration images
    calibration_df['mean_reflectance'] = calibration_df.apply(
        lambda row: detect_panel.get_reflectance(row) if row.cal_in_path else row.mean_reflectance, axis=1
    )
    band_df = calibration_df.groupby('band')[['image_path', 'mean_reflectance', 'autoexposure', 'XMP_index']] \
        .apply(take_closest_image) \
        .reset_index()

    if ils_present:
        band_avg_ils = image_df.groupby('band').ILS.mean().reset_index()
        band_df['ils_scaling_factor'] = band_df.merge(band_avg_ils, on='band').apply(_get_ils_scaling, axis=1)
    else:
        band_df['ils_scaling_factor'] = 1

    coeffs = io.get_zenith_coeffs()

    band_df['slope_coefficient'] = (
        band_df.apply(lambda row: _get_band_coeff(row, coeffs), axis=1) /
        (band_df.mean_reflectance / band_df.autoexposure) *
        band_df.ils_scaling_factor
    )

    image_df = image_df.merge(band_df[['band', 'slope_coefficient']], on='band', how='outer')
    if image_df['slope_coefficient'].isnull().values.any():
        raise FileNotFoundError(
            "Calibration imagery with a visible reference panel was not found for one or more bands."
        )

    return image_df

def compute_correction_coefficient(image_df_row):
    return image_df_row.slope_coefficient / (image_df_row.autoexposure * image_df_row.ILS_ratio)


def adjust_scale(path, max, normalize, uint16_output):
        image_arr = np.asarray(Image.open(path)).astype(np.float32)
        if normalize:
            image_arr = image_arr / max
        if uint16_output:
            image_arr = image_arr * 65535
            image_arr = image_arr.astype(np.uint16)
        tf.imwrite(path, image_arr)


def apply_corrections(image_df_row):
    logger.info("Applying correction to image: %s", image_df_row.image_path)

    image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
    # for images that represent data for multiple bands
    if image_df_row.sensor not in ["6x", "6x_thermal"]:
        # ignore saturated pixels
        saturation_indices = image_arr >= 255
        image_arr[saturation_indices] = np.nan
        # perform band math
        image_arr = detect_panel.isolate_band(image_arr, image_df_row.band_math)

    image_arr = image_arr * image_df_row.correction_coefficient

    return image_arr
