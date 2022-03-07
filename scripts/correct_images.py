import argparse
import logging
import numpy as np
import os
import sys
from tqdm import tqdm

import imgparse
import imgcorrect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Create new `pandas` methods which use `tqdm` progress
# (can use tqdm_gui, optional kwargs, etc.)
tqdm.pandas()


def correct_images(input_path, calibration_id, output_path, no_ils_correct, no_reflectance_correct,
                      delete_original, exiftool_path, output_uint16):

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
    image_df = imgcorrect.create_image_df(input_path, output_path)

    # Get image metadata:
    image_df['EXIF'] = image_df.image_path.apply(imgparse.get_exif_data)

    # Determine sensor type apply sensor specific settings
    image_df = imgcorrect.apply_sensor_settings(image_df)

    # Get autoexposure correction:
    image_df['autoexposure'] = image_df.apply(lambda row: imgparse.get_autoexposure(row.image_path, row.EXIF), axis=1)

    # Split out calibration images, if present:
    if not no_reflectance_correct:
        calibration_df, image_df = imgcorrect.create_cal_df(image_df, calibration_id)

    # Get ILS correction:
    if not no_ils_correct:
        image_df = imgcorrect.compute_ils_correction(image_df)
    else:
        image_df['ILS_ratio'] = 1

    # Get reflectance correction:
    if not no_reflectance_correct:
        image_df = imgcorrect.compute_reflectance_correction(image_df, calibration_df, not no_ils_correct)
    else:
        image_df['slope_coefficient'] = 1

    image_df['correction_coefficient'] = image_df.apply(lambda row: imgcorrect.compute_correction_coefficient(row), axis=1)
    
    # Normalize pixel values in corrected images to original range.
    image_df.correction_coefficient = image_df.correction_coefficient / image_df.groupby('band').correction_coefficient.transform(np.max)

    print(image_df.columns)
    if(output_uint16):
        image_df.correction_coefficient = image_df.apply(lambda row: row.correction_coefficient * 16 if row["sensor"] == "6x" else row.correction_coefficient, axis=1)
        image_df['output_uint16'] = output_uint16

    # Apply corrections:
    image_df = image_df.apply(lambda row: imgcorrect.write_image(imgcorrect.apply_corrections(row), row), axis=1)

    try:
        # Copy EXIF:
        logger.info("Writing EXIF data...")
        # progress_apply is tqdm version of apply
        image_df.progress_apply(lambda row: imgcorrect.copy_exif(row, exiftool_path), axis=1)

        # Delete input imagery if requested:
        if delete_original:
            imgcorrect.delete_all_originals(image_df)

        # Move output imagery to correct output directory:
        if (output_path and (output_path != input_path)) or delete_original:
            imgcorrect.move_corrected_images(image_df)

    except:
        image_df.temp_path.apply(os.remove)
        raise


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_path',
                        help='Path to image files taken from supported sensors. Providing a '
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
    parser.add_argument('--output_uint16', '-u', action='store_true',
                        help="Change output datatype to uint16. Only available for 6x imagery.")

    args = parser.parse_args()

    correct_images(**vars(args))
