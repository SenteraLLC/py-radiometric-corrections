import subprocess
import logging
import os

from glob import glob

logger = logging.getLogger(__name__)


def copy_exif(image_df_row, exiftool_path):
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
