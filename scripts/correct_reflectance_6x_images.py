import argparse
import logging

from correct6x import detect_panel, compute_corrections

def correct_reflectace_6x_images(input_calibration_path, input_images_path, band, output_path):
    mean_dn_df = detect_panel.get_mean_reflectance_df(input_calibration_path)
    optimal_mean_dn_index = compute_corrections.take_closest_image(mean_dn_df)
    optimal_dn = mean_dn_df.at[optimal_mean_dn_index, 'mean_reflectance']
    optimal_autoexposure = mean_dn_df.at[optimal_mean_dn_index, 'autoexposure']
    corrected_mean_dn = compute_corrections.ae_normalize_mean_dn(optimal_dn, optimal_autoexposure)
    slope_coefficient = compute_corrections.empirical_line_function(corrected_mean_dn, band)
    print(slope_coefficient)
    # the next portion should use the slope_coefficient as a multiplier to correct imagery to reflectance.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--input_calibration_path', '-c',
                        help='Path to folder with CAL_* images, taken from a Sentera 6X sensor.')
    parser.add_argument('--input_images_path', '-i',
                        help='Path to folder where the 6X sensor images are stored.')
    parser.add_argument('--band', '-b',
                        help='Band name to proces. Valid strings: [blue, green, red, red edge, nir].')
    parser.add_argument('--output_path', '-o', default=None,
                        help='Path to output folder at which the corrected images will be stored. If not supplied, '
                             'corrected images will be placed into the input directory.')

    args = parser.parse_args()

    correct_reflectace_6x_images(**vars(args))
