"""Input/output operations for Sentera imagery."""

import logging
import os
import re
import shutil
from glob import glob

import numpy as np
import pandas as pd
import tifffile as tf

import imgparse
from imgcorrect import detect_panel
from imgcorrect.sensor_defs import sensor_defs

logger = logging.getLogger(__name__)


def apply_sensor_settings(image_df):
    """Rebuild image dataframe with settings based on sensor model."""
    rows = []
    for _, row in image_df.iterrows():
        for s in sensor_defs:
            # verify image metadata matches that of a supported sensor
            meets_criteria = True
            for key, val in s["criteria"].items():
                if key not in row["EXIF"] or val not in str(row["EXIF"][key]):
                    meets_criteria = False
            if meets_criteria:
                # ignore images that meet ignore_criteria
                if "ignore_criteria" in s:
                    ignore = False
                    for key, val in s["ignore_criteria"].items():
                        if not isinstance(val, list):
                            val = [val]
                        if key in row["EXIF"] and any(
                            [v in str(row["EXIF"][key]) for v in val]
                        ):
                            logger.info("Ignoring %s", row["image_path"])
                            ignore = True
                    if ignore:
                        break

                # apply settings for that sensor
                for key, val in s["settings"].items():
                    row[key] = val

                # if each image contains data for multiple bands, configure accordingly
                if "bands" in s:
                    for band in s["bands"]:
                        band_row = row.copy()
                        band_row["band"] = band[0]
                        band_row["band_math"] = band[1]
                        band_row["XMP_index"] = band[2]
                        band_row["reduce_xmp"] = True
                        band_row["output_path"] = add_band_to_path(
                            row.output_path, band[0]
                        ).replace(".jpg", ".tif")
                        band_row["ID"] = re.findall('(IMG|CAL)_(\d+)', os.path.basename(row.image_path))[0]
                        rows.append(band_row)
                # otherwise, extract bandname from image metadata
                else:
                    row["band"] = imgparse.get_bandnames(row.image_path)[0]
                    row["XMP_index"] = 0
                    row["reduce_xmp"] = False
                    row["ID"] = re.findall('(IMG|CAL)_(\d+)', os.path.basename(row.image_path))[0]
                    rows.append(row)

                break
        else:
            logger.error("Sensor not supported")
            raise Exception("Sensor not supported")
        
    new_image_df = pd.DataFrame(rows)
    images_before_filtering = len(new_image_df.index)
    band_count = len(new_image_df["band"].unique())
    # number of occurences of each ID
    v = new_image_df.ID.value_counts()
    # remove images that don't appear in every band
    new_image_df = new_image_df[new_image_df.ID.isin(v.index[v.eq(band_count)])]
    print(f"Skipping {images_before_filtering - len(new_image_df.index)} images because they don't have data for all bands")

    return new_image_df


def create_image_df(input_path, output_path):
    """Build image dataframe."""
    if not output_path:
        output_path = input_path

    image_df = pd.DataFrame()

    image_df["image_path"] = glob(input_path + "/**/*.tif", recursive=True) + glob(
        input_path + "/**/*.jpg", recursive=True
    )
    image_df["image_root"] = image_df.image_path.apply(os.path.dirname)
    image_df["output_path"] = image_df.image_path.str.replace(
        input_path, output_path, regex=False
    )

    return image_df


def reflectance_if_panel(row):
    """If reflectance panel images are not identifiable by filename, try computing panel reflectance for all images."""
    if not row["cal_in_path"]:
        row["mean_reflectance"], row["aruco_id"] = detect_panel.get_reflectance(row)
    return row


def detect_cal(row, calibration_id):
    """If reflectance panel images are identifiable by filename, identify them. Otherwise, refer to results of reflectance_if_panel()."""
    if row["cal_in_path"]:
        return calibration_id in row["image_path"]
    return not np.isnan(row["mean_reflectance"])


def create_cal_df(image_df, calibration_id):
    """Build calibration image dataframe."""
    image_df = image_df.apply(reflectance_if_panel, axis=1)
    is_cal_image = image_df.apply(lambda row: detect_cal(row, calibration_id), axis=1)

    return image_df.loc[is_cal_image], image_df.loc[~is_cal_image]


def delete_all_originals(image_df):
    """Delete all input images."""
    image_df.image_path.apply(os.remove)


def add_band_to_path(path, band):
    """Add band directory to path just before filename."""
    dirname, base = os.path.split(path)
    return os.path.join(dirname, band, base)


def move_images(image_df_row):
    """Move corrected image to final destination."""
    shutil.move(image_df_row.temp_path, image_df_row.output_path)


def move_corrected_images(image_df):
    """Create output directories if necessary, then move corrected images to final destination."""
    for folder in image_df.output_path.apply(os.path.dirname).unique():
        os.makedirs(folder, exist_ok=True)
    image_df.apply(lambda row: move_images(row), axis=1)


def write_image(image_arr_corrected, image_df_row, temp_dir):
    """Write corrected image to temporary location and record maximum value in case normalization is required."""
    path_list = os.path.normpath(image_df_row.image_path).split(os.path.sep)
    path_list[0] = temp_dir
    temp_path = os.path.join(*path_list)
    if "band_math" in image_df_row.index:
        temp_path = add_band_to_path(temp_path, image_df_row.band).replace(
            ".jpg", ".tif"
        )
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    # noinspection PyTypeChecker
    tf.imwrite(temp_path, image_arr_corrected)

    image_df_row["max_val"] = np.max(image_arr_corrected)
    image_df_row["temp_path"] = temp_path
    return image_df_row


def write_corrections_csv(image_df, file):
    """Write vital correction data from the dataframe to the given csv file."""
    columns = [
        "image_path",
        "independent_ils",
        "band",
        "autoexposure",
        "ILS_ratio",
        "slope_coefficient",
        "correction_coefficient",
    ]
    csv_df = image_df[columns].copy()
    base_dir = os.path.dirname(file)

    # Get the path relative to the output folder
    csv_df["image_path"] = csv_df["image_path"].apply(
        (lambda x: os.path.relpath(x, base_dir))
    )
    csv_df.to_csv(file, index=False)
