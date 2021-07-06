import argparse
import logging
import os
import sys

from glob import glob

import imgparse
import correct6x

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def correct_6x_images(input_path, calibration_id, output_path, no_ils_correct, no_reflectance_correct,
                      delete_original, exiftool_path, register):

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
    image_df['XMP'] = image_df.image_path.apply(imgparse.get_xmp_data)

    # Determine sensor type apply sensor specific settings
    image_df = correct6x.apply_sensor_settings(image_df)

    # Get autoexposure correction:
    image_df['autoexposure'] = image_df.apply(lambda row: imgparse.get_autoexposure(row.image_path, row.EXIF), axis=1)

    # Split out calibration images, if present:
    if not no_reflectance_correct:
        calibration_df, image_df = correct6x.create_cal_df(image_df, calibration_id)

    # Get ILS correction:
    if not no_ils_correct:
        image_df, no_ils_correct = correct6x.compute_ils_correction(image_df)
    else:
        image_df['ILS_ratio'] = 1

    # Get reflectance correction:
    if not no_reflectance_correct:
        image_df = correct6x.compute_reflectance_correction(image_df, calibration_df, not no_ils_correct)
    else:
        image_df['slope_coefficient'] = 1

    # Apply corrections:
    image_df = image_df.apply(lambda row: correct6x.write_image(correct6x.apply_corrections(row), row), axis=1)

    try:
        # Copy EXIF:
        logger.info("Writing EXIF data...")
        image_df.apply(lambda row: correct6x.copy_exif(row, exiftool_path), axis=1)

        # Delete input imagery if requested:
        if delete_original:
            correct6x.delete_all_originals(image_df)

        # Move output imagery to correct output directory:
        if (output_path and (output_path != input_path)) or delete_original:
            correct6x.move_corrected_images(image_df)

        # Perform registration:
        if register:
            from imgreg import multi_spect_dataset_handling
            output_path = output_path or input_path
            dataset_handler = multi_spect_dataset_handling.data_set_handler(
                "cfg/reg_config.ini",
                input_dataset_path=output_path,
                output_dataset_path=os.path.join(output_path, "registered"),
                failure_dataset_path=os.path.join(output_path, "failure")
            )
            dataset_handler.process_all_images(use_init_transform=True, update_from_previous=True)
    except:
        image_df.temp_path.apply(os.remove)
        raise


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_path',
                        help='Path to single-band, single-page .TIF files taken from a Sentera 6X sensor. Providing a '
                             'file path to the original multi-page images is not currently supported. However, '
                             'specifying a folder containing all single-page files in their respective sub-folders '
                             'will cause the script to perform ILS correction recursively throughout each sub-folder.')
    parser.add_argument('--calibration_id', '-c', default='CAL',
                        help='Identifier in the name of the image that denotes it is from the calibration set. '
                             'If not specified, defaults to "CAL".')
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
    parser.add_argument('--register', '-R', action='store_true',
                        help="If selected, perform image registration. Aligned images are output to "
                             "output_path/registered or output_path/failure depending on registration success.")

    args = parser.parse_args()

    correct_6x_images(**vars(args))
