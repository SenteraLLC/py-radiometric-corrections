import bisect
import imgparse
import logging
import os
import re

import numpy as np

from PIL import Image

from correct6x import detect_panel

logger = logging.getLogger(__name__)

ROLLING_AVG_TIMESPAN = '6s'

BLUE_PANEL_COEFFICIENT = 0.1059
GREEN_PANEL_COEFFICIENT = 0.1054
RED_PANEL_COEFFICIENT = 0.1052
RED_EDGE_PANEL_COEFFICIENT = 0.1052
NEAR_INFRARED_COEFFICIENT = 0.1055

BAND_COEFFS = {
    'blue': BLUE_PANEL_COEFFICIENT,
    'green': GREEN_PANEL_COEFFICIENT,
    'red': RED_PANEL_COEFFICIENT,
    're': RED_EDGE_PANEL_COEFFICIENT,
    'NIR': NEAR_INFRARED_COEFFICIENT
}


def take_closest_image(mean_dn_df):
    band_correction_dn_index = bisect.bisect_left(mean_dn_df.loc[:, 'mean_reflectance'], 2048)
    optimal_mean_dn_index = band_correction_dn_index - 1
    return optimal_mean_dn_index


def compute_ils_correction(image_df):
    def _rolling_avg(df):
        return df.astype(float).rolling(ROLLING_AVG_TIMESPAN, closed='both').mean()

    image_df['timestamp'] = image_df.apply(lambda row: imgparse.get_timestamp(row.image_path, row.EXIF), axis=1)
    image_df.set_index('timestamp', drop=True, inplace=True)

    image_df['ILS'] = image_df.image_path.apply(imgparse.get_ils)
    image_df['averaged_ILS'] = image_df.groupby('image_root').ILS.transform(_rolling_avg)

    image_df['ILS_ratio'] = image_df.groupby('image_root').averaged_ILS.transform(lambda df: df / df.mean())

    return image_df['ILS_ratio']


def compute_reflectance_correction(image_df, input_calibration_path):
    def _get_band_coeff(image_root):
        band_name = re.search(r"[A-Za-z]+", os.path.basename(image_root)).group(0).lower()
        return BAND_COEFFS[band_name]

    if not os.path.isdir(input_calibration_path):
        raise FileNotFoundError("To correct for reflectance, a path to calibration images must be specified. "
                                "Specify this path with `--calibration_image_path PATH` or `-c PATH`.")

    mean_dn_df = detect_panel.get_mean_reflectance_df(input_calibration_path)

    optimal_mean_dn_index = take_closest_image(mean_dn_df)
    optimal_dn = mean_dn_df.at[optimal_mean_dn_index, 'mean_reflectance']
    optimal_autoexposure = mean_dn_df.at[optimal_mean_dn_index, 'autoexposure']

    corrected_mean_dn = optimal_dn / optimal_autoexposure
    image_df['slope_coefficient'] = corrected_mean_dn / _get_band_coeff(image_df.image_root)

    return image_df['slope_coefficient']


def apply_corrections(image_df_row):
    logger.info("Applying correction to image: %s", image_df_row.image_path)

    image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
    image_arr /= (image_df_row.autoexposure * image_df_row.ILS_ratio * image_df_row.slope_coefficient)

    return image_arr
