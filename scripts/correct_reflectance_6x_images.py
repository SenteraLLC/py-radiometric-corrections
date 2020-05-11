import argparse
import logging

from corrections import detect_panel


def correct_reflectace_6x_images(input_calibration_path, input_images_path, output_path):
    mean_dn_list = detect_panel.get_mean_reflectance_list(input_calibration_path)
    print(f"Mean list {mean_dn_list}")


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
    