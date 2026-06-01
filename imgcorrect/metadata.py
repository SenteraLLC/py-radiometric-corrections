"""Copy and modify image metadata."""

import logging
import subprocess

from imgparse import MetadataParser

logger = logging.getLogger(__name__)


def copy_exif(image_df_row, exiftool_path):
    """Copy image metadata with necessary changes from original image to corrected image."""
    parser = MetadataParser(image_df_row.image_path)

    command = [
        exiftool_path,
    ]
    make = parser.make()
    if make == "DJI":
        command += ["-config", "cfg/dji.cfg"]
    elif make == "Sentera":
        command += ["-config", "cfg/exiftool.cfg"]
    command += [
        "-overwrite_original",
        "-TagsFromFile",
        image_df_row.image_path,
        "-all",
        "--xmp-Camera:ColorTransform",
        "--xmp-Camera:SunSensor",
        "-xmp-Camera:IsNormalized=1",
        "-xmp-Camera:BlackCurrent=",
        "-xmp-Camera:BlackCurrent=0",
    ]
    if image_df_row.reduce_xmp:
        cent_arr, fwhm_arr = parser.wavelength_data()
        band_arr = parser.bandnames()
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

    # Use CREATE_NO_WINDOW flag on Windows if available (Python 3.7+)
    kwargs = {"capture_output": True}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    results = subprocess.run(command, **kwargs)
    if results.returncode != 0:
        raise ValueError("Exiftool command did not run successfully.")
