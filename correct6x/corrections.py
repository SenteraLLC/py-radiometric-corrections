import imgparse
import logging
import os
import re

import numpy as np

from PIL import Image

from correct6x import detect_panel

logger = logging.getLogger(__name__)

ROLLING_AVG_TIMESPAN = '3s'

BLUE_PANEL_COEFFICIENT = 0.1059
GREEN_PANEL_COEFFICIENT = 0.1054
RED_PANEL_COEFFICIENT = 0.1052
RED_EDGE_PANEL_COEFFICIENT = 0.1052
NEAR_INFRARED_COEFFICIENT = 0.1055

BAND_COEFFS = {
    'blue': BLUE_PANEL_COEFFICIENT,
    'green': GREEN_PANEL_COEFFICIENT,
    'red': RED_PANEL_COEFFICIENT,
    'rededge': RED_EDGE_PANEL_COEFFICIENT,
    'nir': NEAR_INFRARED_COEFFICIENT
}


def take_closest_image(df_grouped_by_band, target=2048):
    return df_grouped_by_band.iloc[(df_grouped_by_band.mean_reflectance - target).abs().argmin()]


def compute_ils_correction(image_df):
    def _rolling_avg(df):
        return df.astype(float).rolling(ROLLING_AVG_TIMESPAN, closed='both').mean()

    image_df['timestamp'] = image_df.apply(lambda row: imgparse.get_timestamp(row.image_path, row.EXIF), axis=1)
    image_df = image_df.set_index('timestamp', drop=True).sort_index()

    image_df['ILS'] = image_df.image_path.apply(imgparse.get_ils)
    image_df['averaged_ILS'] = image_df.groupby('image_root').ILS.transform(_rolling_avg)

    image_df['ILS_ratio'] = image_df.groupby('image_root').averaged_ILS.transform(lambda df: df / df.mean())

    # NOTE: We keep the 'ILS' column here to use it to scale the reflectance correction later.
    return image_df.reset_index().drop(columns=['timestamp', 'averaged_ILS'])


def compute_reflectance_correction(image_df, calibration_df, ils_present):
    def _get_band_coeff(image_root):
        band_name = re.search(r"[A-Za-z]+", os.path.basename(image_root)).group(0).lower()
        return BAND_COEFFS[band_name]

    def _get_ils_scaling(band_row):
        calibration_img_ils = imgparse.get_ils(band_row.image_path)
        return band_row.ILS / calibration_img_ils

    if calibration_df.empty:
        raise FileNotFoundError("No calibration images were found. If not attempting to correct for "
                                "absolute reflectance, set the '--no_reflectance_correct' flag. Otherwise, "
                                "set the calibration image identifier with the '--calibration_id' option.")

    calibration_df['mean_reflectance'] = calibration_df.image_path.apply(detect_panel.get_reflectance)
    band_df = calibration_df.groupby('image_root')[['image_path', 'mean_reflectance', 'autoexposure']] \
        .apply(take_closest_image) \
        .reset_index()

    if ils_present:
        band_avg_ils = image_df.groupby('image_root').ILS.mean().reset_index()
        band_df['ils_scaling_factor'] = band_df.merge(band_avg_ils, on='image_root').apply(_get_ils_scaling, axis=1)
    else:
        band_df['ils_scaling_factor'] = 1

    band_df['slope_coefficient'] = band_df.image_root.apply(_get_band_coeff) / \
        (band_df.mean_reflectance / band_df.autoexposure) * \
        band_df.ils_scaling_factor

    image_df = image_df.merge(band_df[['image_root', 'slope_coefficient']], on='image_root', how='outer')
    if image_df['slope_coefficient'].isnull().values().any():
        raise FileNotFoundError(
            "Calibration imagery with a visible reference panel was not found for one or more bands."
        )

    return image_df

def apply_corrections(image_df_row):
    logger.info("Applying correction to image: %s", image_df_row.image_path)

    image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
    image_arr = (image_arr * image_df_row.slope_coefficient) / (image_df_row.autoexposure * image_df_row.ILS_ratio)

    return image_arr
