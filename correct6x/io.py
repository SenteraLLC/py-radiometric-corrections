import json
import logging
import os
import re

from glob import glob

import cv2 as cv
import numpy as np
import pandas as pd
import tifffile as tf

from correct6x import detect_panel
from correct6x.sensor_defs import sensor_defs


logger = logging.getLogger(__name__)


def apply_sensor_settings(image_df):
    return_df = pd.DataFrame()

    for index, row in image_df.iterrows():
        for s in sensor_defs:
            # verify image metadata matches that of a supported sensor
            meets_criteria = True
            for key, val in s['criteria'].items():
                if key not in row['EXIF'] or val not in str(row['EXIF'][key]):
                    meets_criteria = False
            if meets_criteria:
                # apply settings for that sensor
                for key, val in s['settings'].items():
                    row[key] = val

                # if each image contains data for multiple bands, configure accordingly
                if 'bands' in s:
                    for band in s['bands']:
                        row['band'] = band[0]
                        row['band_math'] = band[1]
                        row['output_path'] = add_band_to_path(row.output_path, band[0]).replace('.jpg', '.tif')
                        return_df = return_df.append(row, ignore_index=True)
                # otherwise, assume band is indicated in root folder name
                else:
                    row['band'] = re.search(r"[A-Za-z]+", os.path.basename(row.image_root)).group(0).lower()
                    return_df = return_df.append(row, ignore_index=True)

                break
        else:
            logger.error('Sensor not supported')
            raise Exception('Sensor not supported')

    return return_df
        
    
def create_image_df(input_path, output_path):
    if not output_path:
        output_path = input_path

    image_df = pd.DataFrame()

    image_df['image_path'] = (
        glob(input_path + '/**/*.tif', recursive=True) + 
        glob(input_path + '/**/*.jpg', recursive=True)
    )
    image_df['image_root'] = image_df.image_path.apply(os.path.dirname)
    image_df['output_path'] = image_df.image_path.str.replace(input_path, output_path, regex=False)

    return image_df


def reflectance_if_panel(row):
    # if which images contain reflectance panels is not indicated via file name (ex. includes 'CAL')
    # compute reflectance now, and know that images for which reflectance was found are calibration images
    if not row['cal_in_path']:
        row['mean_reflectance'] = detect_panel.get_reflectance(row)
    return row


def detect_cal(row, calibration_id):
    # if calibration images are identifiable by file name, identify them that way
    if row['cal_in_path']:
        return calibration_id in row['image_path']
    # otherwise, see if previous operation detected a reflectance panel
    return not np.isnan(row['mean_reflectance'])


def create_cal_df(image_df, calibration_id):
    # calculate reflectance if necessary
    image_df = image_df.apply(reflectance_if_panel, axis=1)
    is_cal_image = image_df.apply(lambda row: detect_cal(row, calibration_id), axis=1)
    return image_df.loc[is_cal_image], image_df.loc[~is_cal_image]


def delete_all_originals(image_df):
    image_df.image_path.apply(os.remove)


def add_band_to_path(path, band):
    dir, base = os.path.split(path)
    return os.path.join(dir, band, base)


def move_images(image_df_row):
    os.rename(image_df_row.temp_path, image_df_row.output_path)


def move_corrected_images(image_df):
    for folder in image_df.output_path.apply(os.path.dirname).unique():
        if not os.path.isdir(folder):
            os.makedirs(folder)
    image_df.apply(lambda row: move_images(row), axis=1)


def write_image(image_arr_corrected, image_df_row):
    if image_df_row.sensor == '6x':
        temp_path = image_df_row.image_path.replace('.tif', '_f32.tif')
    else:
        temp_path = add_band_to_path(image_df_row.image_path, image_df_row.band).replace('.jpg', '.tif')
        if not os.path.isdir(os.path.dirname(temp_path)):
            os.makedirs(os.path.dirname(temp_path))
    # noinspection PyTypeChecker
    tf.imwrite(temp_path, image_arr_corrected)

    image_df_row['temp_path'] = temp_path
    return image_df_row
