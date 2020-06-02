import argparse
import logging
import os
import re
import sys

# The "unofficial" supported version:
import exiftool.pyexiftool as exiftool

# The "official" old version:
# import exiftool

import tifffile as tf
import pandas as pd
import numpy as np

from glob import glob
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

UNNEEDED_TAGS = [
    'ImageWidth',
    'ImageLength',
    'BitsPerSample',
    'Compression',
    'PhotometricInterpretation',
    'StripOffsets',
    'SamplesPerPixel',
    'RowsPerStrip',
    'StripByteCounts',
    'XResolution',
    'YResolution',
    'ResolutionUnit',
    'PlanarConfiguration',
    'Software',
    'ExifTag', # Handled by ExifTool
    'GPSTag' # Handled by ExifTool
]


def set_output_names(input_path, output_path):

    if not output_path:
        output_path = input_path

    image_df = pd.DataFrame()

    image_df['image_path'] = glob(input_path + '/**/*.tif', recursive=True)
    image_df['output_path'] = image_df.image_path.str.replace(input_path, output_path, regex=False)

    return image_df


def load_images(image_df):
    image_df['image_obj'] = image_df.image_path.apply(tf.TiffFile)

    return image_df


def find_ils_values(image_df):

    def _extract_ils(image_obj_row):
        ils_re = re.compile(r"<Camera:SunSensor>\n(?: *|\t)<rdf:Seq>\n(?: *|\t)<rdf:li>([0-9]+.[0-9]+)")
        match = ils_re.findall(image_obj_row.pages[0].tags[700].value)
        if match:
            return match[0]

    image_df['ILS_val'] = image_df.image_obj.apply(_extract_ils)

    return image_df


def find_image_timestamps(image_df):

    def _extract_timestamps(image_obj_row):
        return image_obj_row.pages[0].tags[306].value

    image_df['image_timestamp'] = pd.to_datetime(image_df.image_obj.apply(_extract_timestamps),
                                                 format='%Y:%m:%d %H:%M:%S')

    return image_df


def compute_rolling_average(image_df):

    def _rolling_avg(df):
        return df.astype(float).rolling('6s', closed='both').mean()

    image_df.set_index('image_timestamp', drop=True, inplace=True)

    image_df['image_root'] = image_df.image_path.apply(os.path.dirname)
    image_df['averaged_ILS_val'] = image_df.groupby('image_root')['ILS_val'].transform(_rolling_avg)

    return image_df


def calculate_correction_factors(image_df):

    def _calc_adj_dn(image_exif_row):
        exp_time = image_exif_row['ExposureTime'][0] / \
                   image_exif_row['ExposureTime'][1]
        iso = image_exif_row['ISOSpeedRatings'] / 100

        return exp_time * iso

    def _load_exif(image_obj_row):
        return image_obj_row.pages[0].tags[34665].value

    image_df['EXIF'] = image_df.image_obj.apply(_load_exif)
    image_df['ILS_ratio'] = image_df.groupby('image_root').averaged_ILS_val.transform(lambda df: df / df.mean())
    image_df['AE_correction'] = image_df.EXIF.apply(_calc_adj_dn)

    return image_df


def get_image_metadata(image_df):

    def _form_metadata_list(image_obj_row):
        return [(tag.code, tag.dtype.replace('1', ''), tag.count, tag.value, True)
                for tag in image_obj_row.pages[0].tags
                if tag.name not in UNNEEDED_TAGS]

    image_df['image_meta'] = image_df.image_obj.apply(_form_metadata_list)

    return image_df


def adjust_and_write_image_values(image_df, no_ils_correct):

    def _apply_correction(image_df_row, no_ils_correct):
        logger.info("Applying correction to image: %s", image_df_row.image_path)

        image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
        image_arr_ae = image_arr / image_df_row.AE_correction

        if no_ils_correct:
            return image_arr_ae
        else:
            return image_arr_ae / image_df_row.ILS_ratio

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

    image_df.apply(lambda row: _write_image(_apply_correction(row, no_ils_correct), row), axis=1)
    image_df.image_obj.apply(lambda obj: obj.close())


def copy_exif_metadata(input_path, exiftool_path):
    logger.info("Writing EXIF data...")
    try:
        with exiftool.ExifTool(executable_=exiftool_path) as et:
            et.execute(b"-overwrite_original",
                       b"-r",
                       b"-TagsFromFile",
                       exiftool.fsencode(os.path.join('%d', '%-.4f.tif')),
                       exiftool.fsencode(input_path),
                       b"-gps:all",
                       b"-exif:all")
    except AttributeError:
        for file in glob(input_path + '/**/*_f32.tif', recursive=True):
            os.remove(file)
        raise FileNotFoundError("Couldn't find ExifTool executable.")


def delete_all_originals(image_df):
    image_df.image_path.apply(os.remove)


def move_corrected_images(image_df):

    def _move_images(image_df_row):
        os.rename(image_df_row.image_path.replace('.tif', '_f32.tif'), image_df_row.output_path)

    for folder in image_df.output_path.apply(os.path.dirname).unique():
        if not os.path.isdir(folder):
            os.makedirs(folder)

    image_df.apply(lambda row: _move_images(row), axis=1)


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

    image_df = set_output_names(input_path, output_path)
    image_df = load_images(image_df)
    image_df = find_ils_values(image_df)
    image_df = find_image_timestamps(image_df)
    image_df = compute_rolling_average(image_df)
    image_df = calculate_correction_factors(image_df)
    image_df = get_image_metadata(image_df)

    adjust_and_write_image_values(image_df, no_ils_correct)
    copy_exif_metadata(input_path, exiftool_path)

    if delete_original:
        delete_all_originals(image_df)

    if (output_path and (output_path != input_path)) or delete_original:
        move_corrected_images(image_df)


if __name__ == '__main__':

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
