import bisect
import os
import numpy as np
import logging
from PIL import Image

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


def ae_normalize_mean_dn(optimal_mean_dn, autoexposure):
    normalized_mean_dn = optimal_mean_dn / autoexposure
    return normalized_mean_dn


def get_band_coeff(input_path):
    path = os.path.dirname(input_path)
    band = os.path.basename(path)
    band_coeff = BAND_COEFFS[band]
    return band_coeff


def empirical_line_function(normalized_mean_dn, band_coeff):
    slope_coefficient = normalized_mean_dn / band_coeff
    return slope_coefficient


def adjust_and_write_image_values(image_df, no_autoexposure, slope_coefficient):

    def _apply_correction(image_df_row, no_autoexposure):
        logger.info("Applying correction to image: %s", image_df_row.image_path)

        image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
        image_arr_ae = image_arr / image_df_row.AE_correction
        if no_autoexposure:
            return image_arr/slope_coefficient
        else:
            return image_arr_ae / (image_df_row.AE_correction * slope_coefficient)


    def _write_image(image_arr_corrected, image_df_row):

        tags = image_df_row.image_obj.pages[0].tags

        x_res = tags['XResolution'].value
        y_res = tags['YResolution'].value
        res_unit = tags['ResolutionUnit'].value
        planar_config = tags['PlanarConfiguration'].value
        software = tags['Software'].value

        # noinspection PyTypeChecker
        tf.imwrite(image_df_row.image_path.replace('.tif', '_f32.tif'),
                   image_arr_corrected,
                   resolution=(x_res, y_res, res_unit),
                   planarconfig=planar_config,
                   software=software,
                   extratags=image_df_row.image_meta)

    image_df.apply(lambda row: _write_image(_apply_correction(row, no_autoexposure), row), axis=1)
    image_df.image_obj.apply(lambda obj: obj.close())






