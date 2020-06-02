import argparse
import logging

from correct6x import detect_panel, compute_corrections
from scripts import correct_ils_6x_images


def correct_reflectance_6x_images(
        no_autoexposure,
        input_calibration_path,
        input_images_path,
        output_path,
        delete_original
):
    mean_dn_df = detect_panel.get_mean_reflectance_df(input_calibration_path)
    optimal_mean_dn_index = compute_corrections.take_closest_image(mean_dn_df)
    optimal_dn = mean_dn_df.at[optimal_mean_dn_index, 'mean_reflectance']
    optimal_autoexposure = mean_dn_df.at[optimal_mean_dn_index, 'autoexposure']
    corrected_mean_dn = compute_corrections.ae_normalize_mean_dn(optimal_dn, optimal_autoexposure)
    band_coeff = compute_corrections.get_band_coeff(input_images_path)
    slope_coefficient = compute_corrections.empirical_line_function(corrected_mean_dn, band_coeff)

    image_df = correct_ils_6x_images.set_output_names(input_images_path, output_path)
    image_df = correct_ils_6x_images.load_images(image_df)
    image_df = correct_ils_6x_images.get_image_metadata(image_df)

    compute_corrections.adjust_and_write_image_values(image_df, no_autoexposure, slope_coefficient)
    correct_ils_6x_images.copy_exif_metadata(input_images_path)

    if delete_original:
        correct_ils_6x_images.delete_all_originals(image_df)

    if (output_path and (output_path != input_images_path)) or delete_original:
        correct_ils_6x_images.move_corrected_images(image_df)


if __name__ == '__main__':

    parser.add_argument("--no_autoexposure",
                        help="don't correct for autoexposure, turn on if it has already been done in another script.")
    parser.add_argument('--input_calibration_path', '-c',
                        help='Path to folder with CAL_* images, taken from a Sentera 6X sensor.')
    parser.add_argument('--input_images_path', '-i',
                        help='Path to folder where the 6X sensor images are stored.')
    parser.add_argument('--output_path', '-o', default=None,
                        help='Path to output folder at which the corrected images will be stored. If not supplied, '
                             'corrected images will be placed into the input directory.')
    parser.add_argument('--delete_original', '-d', action='store_true',
                        help='Overwrite original 12-bit images with the corrected versions. If selected, corrected '
                             'images are renamed to their original names. If not, an extension is added.')

    args = parser.parse_args()
    correct_reflectace_6x_images(**vars(args))
