"""Copy and modify image metadata."""

import logging
import subprocess

import imgparse

logger = logging.getLogger(__name__)


def copy_exif(image_df_row, exiftool_path):
    """Copy image metadata with necessary changes from original image to corrected image."""
    command = [
        exiftool_path,
        "-config",
        "cfg/exiftool.cfg",
        "-overwrite_original",
        "-TagsFromFile",
        image_df_row.image_path,
        "-all",
        "--xmp-Camera:ColorTransform",
        "--xmp-Camera:SunSensor",
        "-xmp-Camera:IsNormalized=1",
    ]
    if image_df_row.reduce_xmp:
        cent_arr, fwhm_arr = imgparse.get_wavelength_data(image_df_row.image_path)
        band_arr = imgparse.get_bandnames(image_df_row.image_path)
        i = int(image_df_row.XMP_index)
        command += [
            "-xmp-Camera:BandName=",
            "-xmp-Camera:CentralWavelength=",
            "-xmp-Camera:WavelengthFWHM=",
            f"-xmp-Camera:BandName={band_arr[i]}",
            f"-xmp-Camera:CentralWavelength={cent_arr[i]}",
            f"-xmp-Camera:WavelengthFWHM={fwhm_arr[i]}",
        ]
    command.append(image_df_row.temp_path)

    results = subprocess.run(command, capture_output=True)
    if results.returncode != 0:
        raise ValueError("Exiftool command did not run successfully.")
