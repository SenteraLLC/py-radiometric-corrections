import subprocess
import logging

import imgparse

logger = logging.getLogger(__name__)


def copy_exif(image_df_row, exiftool_path):
    # copy over all metadata exactly as it is
    copy_command = subprocess.run(
        [
            exiftool_path,
            "-overwrite_original",
            "-TagsFromFile",
            image_df_row.image_path,
            image_df_row.temp_path,
            "-xmp",
            "-exif",
            "-all",
        ],
        capture_output=True
    )

    if copy_command.returncode != 0:
        raise ValueError("Exiftool copy command did not run successfully.")

    edit_command = [
        exiftool_path,
        "-config",
        "cfg/exiftool.cfg",
        "-overwrite_original",
        "-xmp-Camera:ColorTransform=",
        "-xmp-Camera:SunSensor=",
        "-xmp-Camera:IsNormalized=1"
    ]

    if image_df_row.reduce_xmp:
        cent_arr, fwhm_arr = imgparse.get_wavelength_data(image_df_row.image_path)
        band_arr = imgparse.get_bandnames(image_df_row.image_path)
        i = int(image_df_row.XMP_index)
        edit_command += [
            f"-xmp-Camera:BandName={band_arr[i]}",
            f"-xmp-Camera:CentralWavelength={cent_arr[i]}",
            f"-xmp-Camera:WavelengthFWHM={fwhm_arr[i]}",
        ]

    edit_command.append(image_df_row.temp_path)
    edit_results = subprocess.run(edit_command, capture_output=True)

    if edit_results.returncode != 0:
        print(edit_results)
        raise ValueError("Exiftool edit command did not run successfully.")
