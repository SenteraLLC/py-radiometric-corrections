import argparse
import logging
import os
import sys

from glob import glob

import imgparse
import correct6x

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def correct_6x_images(input_path, calibration_image_path, output_path, no_ils_correct, no_reflectance_correct,
                      delete_original, exiftool_path):

    def _flag_format(flag):
        if flag:
            return "Enabled"
        else:
            return "Disabled"

    if not exiftool_path:
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app
            # path into variable _MEIPASS'.
            exiftool_path = os.path.join(sys._MEIPASS, 'exiftool.exe')
        else:
            exiftool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         'exiftool',
                                         'exiftool.exe')
        logger.info("Using bundled executable. Setting ExifTool path to %s", exiftool_path)

    logger.info("ILS corrections: %s", _flag_format(not no_ils_correct))
    logger.info("Delete original: %s", _flag_format(delete_original))

    # Read images:
    image_df = correct6x.create_image_df(input_path, output_path)

    # Get image metadata:
    image_df['EXIF'] = image_df.image_path.apply(imgparse.get_exif_data)

    # Note: These calls will get cleaner with some `imgparse` improvements I have in mind:
    # Get autoexposure correction:
    image_df['autoexposure'] = image_df.apply(lambda row: imgparse.get_autoexposure(row.image_path, row.EXIF), axis=1)

    # Get ILS correction:
    if not no_ils_correct:
        image_df['ILS_ratio'] = correct6x.compute_ils_correction(image_df)
    else:
        image_df['ILS_ratio'] = 1

    # Get reflectance correction:
    if not no_reflectance_correct:
        image_df['slope_coefficient'] = correct6x.compute_reflectance_correction(image_df, calibration_image_path)
    else:
        image_df['slope_coefficient'] = 1

    # Apply corrections:
    image_df.apply(lambda row: correct6x.write_image(correct6x.apply_corrections(row), row), axis=1)

    # Copy EXIF:
    copy_command = correct6x.copy_exif(input_path, exiftool_path)
    if copy_command.returncode != 0:
        for file in glob(input_path + '/**/*_f32.tif', recursive=True):
            os.remove(file)
        raise ValueError("Exiftool copy command did not run successfully.")

    if delete_original:
        correct6x.delete_all_originals(image_df)

    if (output_path and (output_path != input_path)) or delete_original:
        correct6x.move_corrected_images(image_df)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_path',
                        help='Path to single-band, single-page .TIF files taken from a Sentera 6X sensor. Providing a '
                             'file path to the original multi-page images is not currently supported. However, '
                             'specifying a folder containing all single-page files in their respective sub-folders '
                             'will cause the script to perform ILS correction recursively throughout each sub-folder.')
    parser.add_argument('--calibration_image_path', '-c',
                        help='Path to folder of calibration images used to convert imagery to absolute reflectance. '
                             'Only required if performing reflectance correction.')
    parser.add_argument('--output_path', '-o', default=None,
                        help='Path to output folder at which the corrected images will be stored. If not supplied, '
                             'corrected images will be placed into the input directory.')
    parser.add_argument('--no_ils_correct', '-i', action='store_true',
                        help="If selected, ILS correction will not be applied to the images.")
    parser.add_argument('--no_reflectance_correct', '-r', action='store_true',
                        help="If selected, reflectance correction will not be applied to the images.")
    parser.add_argument('--delete_original', '-d', action='store_true',
                        help='Overwrite original 12-bit images with the corrected versions. If selected, corrected '
                             'images are renamed to their original names. If not, an extension is added.')
    parser.add_argument('--exiftool_path', '-e', default=None,
                        help="Path to ExifTool executable. ExifTool is required for the conversion; if not passed, "
                             "the script will use a bundled ExifTool executable.")

    args = parser.parse_args()
    correct_6x_images(**vars(args))
