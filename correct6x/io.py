import os

from glob import glob

import pandas as pd
import tifffile as tf

import imgparse

# Since the `form_metadata_list` function is likely gone, this can probably be removed too:
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


def create_image_df(input_path, output_path):
    if not output_path:
        output_path = input_path

    image_df = pd.DataFrame()

    image_df['image_path'] = glob(input_path + '/**/*.tif', recursive=True)
    image_df['output_path'] = image_df.image_path.str.replace(input_path, output_path, regex=False)

    return image_df


def write_image(image_arr_corrected, image_df_row):

    # Probably not necessary -- likely has already been loaded in
    exif_data = imgparse.get_exif_data(image_df_row.image_path)

    x_res = exif_data['Image XResolution'].value
    y_res = exif_data['Image YResolution'].value
    res_unit = exif_data['Image ResolutionUnit'].value
    planar_config = exif_data['Image PlanarConfiguration'].value
    software = exif_data['Image Software'].value

    # noinspection PyTypeChecker
    tf.imwrite(image_df_row.image_path.replace('.tif', '_f32.tif'),
               image_arr_corrected,
               resolution=(x_res, y_res, res_unit),
               planarconfig=planar_config,
               software=software)


def move_images(image_df_row):
    os.rename(image_df_row.image_path.replace('.tif', '_f32.tif'), image_df_row.output_path)
