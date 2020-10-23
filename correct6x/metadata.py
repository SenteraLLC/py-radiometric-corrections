import subprocess
import logging
import os

from glob import glob

logger = logging.getLogger(__name__)


def copy_exif(source_dir, exiftool_path):
    logger.info("Writing EXIF data...")
    copy_command = subprocess.run([exiftool_path,
                                   "-overwrite_original",
                                   "-r",
                                   "-TagsFromFile",
                                   os.path.join("%d", "%-.4f.tif"),
                                   source_dir,
                                   "-xmp",
                                   "-exif",
                                   "-all",
                                   "-ext tif"],
                                  capture_output=True)

    return copy_command
