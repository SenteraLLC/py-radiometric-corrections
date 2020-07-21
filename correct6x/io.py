import logging
import os

from glob import glob

import pandas as pd
import tifffile as tf


logger = logging.getLogger(__name__)


def create_image_df(input_path, output_path):
    if not output_path:
        output_path = input_path

    image_df = pd.DataFrame()

    image_df['image_path'] = glob(input_path + '/**/*.tif', recursive=True)
    image_df['image_root'] = image_df.image_path.apply(os.path.dirname)
    image_df['output_path'] = image_df.image_path.str.replace(input_path, output_path, regex=False)

    return image_df


def delete_all_originals(image_df):
    image_df.image_path.apply(os.remove)


def move_images(image_df_row):
    os.rename(image_df_row.image_path.replace('.tif', '_f32.tif'), image_df_row.output_path)


def move_corrected_images(image_df):
    for folder in image_df.output_path.apply(os.path.dirname).unique():
        if not os.path.isdir(folder):
            os.makedirs(folder)
    image_df.apply(lambda row: move_images(row), axis=1)


def write_image(image_arr_corrected, image_df_row):

    # noinspection PyTypeChecker
    tf.imwrite(image_df_row.image_path.replace('.tif', '_f32.tif'),
               image_arr_corrected)
