import csv
import logging
import os
import re
import shutil

from glob import glob

import numpy as np
import pandas as pd
import tifffile as tf

from imgcorrect import detect_panel
from imgcorrect.sensor_defs import sensor_defs


logger = logging.getLogger(__name__)


def apply_sensor_settings(image_df):
    rows = []

    for index, row in image_df.iterrows():
        for s in sensor_defs:
            # verify image metadata matches that of a supported sensor
            meets_criteria = True
            for key, val in s['criteria'].items():
                if key not in row['EXIF'] or val not in str(row['EXIF'][key]):
                    meets_criteria = False
            if meets_criteria:
                # ignore images that meet ignore_criteria
                if 'ignore_criteria' in s:
                    ignore = False
                    for key, val in s['ignore_criteria'].items():
                        if key in row['EXIF'] and val in str(row['EXIF'][key]):
                            logger.info(f"Ignoring {row['image_path']}")
                            ignore = True
                    if ignore:
                        break

                # apply settings for that sensor
                for key, val in s['settings'].items():
                    row[key] = val

                # if each image contains data for multiple bands, configure accordingly
                if 'bands' in s:
                    for band in s['bands']:
                        row['band'] = band[0]
                        row['band_math'] = band[1]
                        row['XMP_index'] = band[2]
                        row['reduce_xmp'] = True
                        row['output_path'] = add_band_to_path(row.output_path, band[0]).replace('.jpg', '.tif')
                        rows.append(row)
                # otherwise, assume band is indicated in root folder name
                else:
                    row['band'] = re.search(r"[A-Za-z]+", os.path.basename(row.image_root)).group(0).lower()
                    row['XMP_index'] = 0
                    row['reduce_xmp'] = False
                    rows.append(row)

                break
        else:
            logger.error('Sensor not supported')
            raise Exception('Sensor not supported')

    return pd.DataFrame(rows)
        
    
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
    shutil.move(image_df_row.temp_path, image_df_row.output_path)


def move_corrected_images(image_df):
    for folder in image_df.output_path.apply(os.path.dirname).unique():
        os.makedirs(folder, exist_ok=True)
    image_df.apply(lambda row: move_images(row), axis=1)


def write_image(image_arr_corrected, image_df_row, temp_dir):
    path_list = os.path.normpath(image_df_row.image_path).split(os.path.sep)
    path_list[0] = temp_dir
    temp_path = os.path.join(*path_list)
    if 'band_math' in image_df_row.index:
        temp_path = add_band_to_path(temp_path, image_df_row.band).replace('.jpg', '.tif')
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    # noinspection PyTypeChecker
    tf.imwrite(temp_path, image_arr_corrected)

    image_df_row['max_val'] = np.max(image_arr_corrected)
    image_df_row['temp_path'] = temp_path
    return image_df_row


def get_zenith_coeffs():
    arr = np.empty(2501, dtype=float)
    with open("zenith_co.csv", newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            arr[int(row[0])] = float(row[1]) / 100 # convert from percentages
    return arr
