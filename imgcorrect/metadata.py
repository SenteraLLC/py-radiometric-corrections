"""Copy and modify image metadata."""

import logging

from imgparse import MetadataParser

logger = logging.getLogger(__name__)


def copy_exif(image_df_row, exiftool_session):
    """Copy image metadata with necessary changes from original image to corrected image."""
    parser = MetadataParser(image_df_row.image_path)

    command = []
    if image_df_row.band.lower() == "lwir":
        command += [
            "-overwrite_original",
            "-TagsFromFile",
            image_df_row.image_path,
            "-xmp",
            "-exif",
            "-all",
        ]
    else:
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
    command.append(str(image_df_row.temp_path))

    exiftool_session.execute(*command)
    if exiftool_session.last_status != 0:
        raise ValueError(f"ExifTool failed: {exiftool_session.last_stderr}")
