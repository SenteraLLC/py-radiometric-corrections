import os

from glob import glob

import pandas as pd
import tifffile as tf


def create_image_df(input_path, output_path):
    if not output_path:
        output_path = input_path

    image_df = pd.DataFrame()

    image_df['image_path'] = glob(input_path + '/**/*.tif', recursive=True)
    image_df['output_path'] = image_df.image_path.str.replace(input_path, output_path, regex=False)

    return image_df


def write_image(image_arr_corrected, image_df_row):

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


def move_images(image_df_row):
    os.rename(image_df_row.image_path.replace('.tif', '_f32.tif'), image_df_row.output_path)