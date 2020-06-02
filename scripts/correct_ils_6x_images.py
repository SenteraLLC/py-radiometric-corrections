import argparse
import logging
import os
import sys

import tifffile as tf
import pandas as pd

import correct6x

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

ROLLING_AVG_TIMESPAN = '6s'


# I think I'll make these freestanding `apply` calls and save the function definition:
def load_images(image_df):
    image_df['image_exif'] = image_df.image_path.apply(imgparse.get_exif_data)
    return image_df


def find_ils_values(image_df):
    image_df['ILS_val'] = image_df.image_path.apply(imgparse.get_ils)
    return image_df


def find_image_timestamps(image_df):
    image_df['image_timestamp'] = image_df.image_obj.apply(imgparse.get_timestamp)
    return image_df
# --------------------------------------------------------------------------------------


def compute_ils_correction(image_df):

    def _rolling_avg(df):
        return df.astype(float).rolling(ROLLING_AVG_TIMESPAN, closed='both').mean()

    image_df.set_index('image_timestamp', drop=True, inplace=True)

    image_df['image_root'] = image_df.image_path.apply(os.path.dirname)
    image_df['averaged_ILS_val'] = image_df.groupby('image_root').ILS_val.transform(_rolling_avg)
    image_df['ILS_ratio'] = image_df.groupby('image_root').averaged_ILS_val.transform(lambda df: df / df.mean())

    return image_df


def compute_ae_correction(image_df):
    image_df['AE_correction'] = image_df.image_exif.apply(imgparse.get_autoexposure)
    return image_df


def adjust_and_write_image_values(image_df, no_ils_correct):
    image_df.apply(lambda row: correct6x.io.write_image(correct6x.corrections.apply_correction(row,
                                                                                               no_ils_correct),
                                                        row),
                   axis=1)
    image_df.image_obj.apply(lambda obj: obj.close())


def delete_all_originals(image_df):
    image_df.image_path.apply(os.remove)


def move_corrected_images(image_df):
    for folder in image_df.output_path.apply(os.path.dirname).unique():
        if not os.path.isdir(folder):
            os.makedirs(folder)
    image_df.apply(lambda row: correct6x.io.move_images(row), axis=1)


def correct_ils_6x_images(input_path, output_path, no_ils_correct, delete_original, exiftool_path):

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

    image_df = correct6x.io.create_image_df(input_path, output_path)
    image_df = load_images(image_df)
    image_df = find_ils_values(image_df)
    image_df = find_image_timestamps(image_df)
    image_df = compute_rolling_average(image_df)
    image_df = calculate_correction_factors(image_df)

    adjust_and_write_image_values(image_df, no_ils_correct)

    if delete_original:
        delete_all_originals(image_df)

    if (output_path and (output_path != input_path)) or delete_original:
        move_corrected_images(image_df)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--no_autoexposure",
                        help="don't correct for autoexposure, turn on if it has already been done in another script.")
    parser.add_argument('input_path',
                        help='Path to single-band, single-page .TIF files taken from a Sentera 6X sensor. Providing a '
                             'file path to the original multi-page images is not currently supported. However, '
                             'specifying a folder containing all single-page files in their respective sub-folders '
                             'will cause the script to perform ILS correction recursively throughout each sub-folder.')
    parser.add_argument('--output_path', '-o', default=None,
                        help='Path to output folder at which the corrected images will be stored. If not supplied, '
                             'corrected images will be placed into the input directory.')
    parser.add_argument('--no_ils_correct', '-i', action='store_true',
                        help="If selected, ILS correction will not be applied to the images.")
    parser.add_argument('--delete_original', '-d', action='store_true',
                        help='Overwrite original 12-bit images with the corrected versions. If selected, corrected '
                             'images are renamed to their original names. If not, an extension is added.')
    parser.add_argument('--exiftool_path', '-e', default=None,
                        help="Path to ExifTool executable. ExifTool is required for the conversion; if not passed, "
                             "the script will use a bundled ExifTool executable.")

    args = parser.parse_args()
    correct_ils_6x_images(**vars(args))
