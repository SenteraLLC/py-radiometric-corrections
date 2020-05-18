import argparse
import logging
import bisect
from corrections import detect_panel

BLUE_PANEL_COEFFICIENT = 0.1059
GREEN_PANEL_COEFFICIENT = 0.1054
RED_PANEL_COEFFICIENT = 0.1052
RED_EDGE_PANEL_COEFFICIENT = 0.1052
NEAR_INFRARED_COEFFICIENT = 0.1055

BAND_COEFFS = {
    'blue': BLUE_PANEL_COEFFICIENT,
    'green': GREEN_PANEL_COEFFICIENT,
    'red': RED_PANEL_COEFFICIENT,
    'red edge': RED_EDGE_PANEL_COEFFICIENT,
    'nir': NEAR_INFRARED_COEFFICIENT
}


def take_closest_image(mean_dn_list):
    band_correction_dn = bisect.bisect_left(mean_dn_list, 2048)
    optimal_mean_dn = mean_dn_list[band_correction_dn - 1]
    return optimal_mean_dn


# I need mean_dn_values from detect_panel.py as a data frame with additional columns of autoexposure and iso/100.
def ae_normalize_mean_dn(optimal_mean_dn, autoexposure, iso):
    normalized_mean_dn = optimal_mean_dn / (autoexposure * iso)
    return normalized_mean_dn


def empirical_line_function(normalized_mean_dn, band):
    slope_coefficient = normalized_mean_dn / BAND_COEFFS[band]
    return slope_coefficient


def correct_reflectace_6x_images(input_calibration_path, input_images_path, output_path):
    mean_dn_list = detect_panel.get_mean_reflectance_list(input_calibration_path)
    print(f"Mean list {mean_dn_list}")
    optimal_mean_dn = take_closest_image(mean_dn_list)
    corrected_mean_dn = ae_corrected_mean_dn(optimal_mean_dn, autoexposure, iso)
    slope_coefficient = empirical_line_function(corrected_mean_dn, band)

    # the next portion should use the slope_coefficient as a multiplier to correct imagery to reflectance.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_calibration_path', '-c',
                        help='Path to folder with CAL_* images, taken from a Sentera 6X sensor.')
    parser.add_argument('--input_images_path', '-i',
                        help='Path to folder where the 6X sensor images are stored.')
    parser.add_argument('--output_path', '-o', default=None,
                        help='Path to output folder at which the corrected images will be stored. If not supplied, '
                             'corrected images will be placed into the input directory.')

    args = parser.parse_args()

    correct_reflectace_6x_images(**vars(args))
