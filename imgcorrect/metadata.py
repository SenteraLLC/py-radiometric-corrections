"""Copy and modify image metadata."""

import logging
import subprocess

from imgparse import MetadataParser

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
    ]
    # DJI Mavic 3M
    if image_df_row.sensor == "M3M":
        BAND_PARAMS = {
            "Green": {
                "name": "Green",
                "wavelength": 560,
                "fwhm": 16,
                # "freq": "560(+/-16)nm",
            },
            "Red": {
                "name": "Red",
                "wavelength": 650,
                "fwhm": 16,
                # "freq": "650(+/-16)nm",
            },
            "RedEdge": {
                "name": "RedEdge",
                "wavelength": 730,
                "fwhm": 16,
                # "freq": "730(+/-16)nm",
            },
            "NIR": {
                "name": "NIR",
                "wavelength": 860,
                "fwhm": 26,
                # "freq": "860(+/-26)nm",
            },
        }
        band_info = BAND_PARAMS[image_df_row.band]

        command += [
            "-BandName=",
            "-CentralWavelength=",
            "-WavelengthFWHM=",
            f"-BandName={band_info['name']}",
            f"-CentralWavelength={band_info['wavelength']}",
            f"-WavelengthFWHM={band_info['fwhm']}",
            # f"-BandFreq={band_info['freq']}",
            f"-IsNormalized=1",
        ]
    else:
        command += [
            "--xmp-Camera:ColorTransform",
            "--xmp-Camera:SunSensor",
            "-xmp-Camera:IsNormalized=1",
            "-xmp-Camera:BlackCurrent=",
            "-xmp-Camera:BlackCurrent=0",
        ]

        if image_df_row.reduce_xmp:
            parser = MetadataParser(image_df_row.image_path)
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
