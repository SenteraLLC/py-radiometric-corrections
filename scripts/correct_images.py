"""Radiometric corrections for Sentera sensors."""

import argparse
import logging
import os
import sys

from imgcorrect import corrections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_path",
        help="Path to image files taken from supported sensors. Providing a "
        "file path to the original multi-page images is not currently supported. However, "
        "specifying a folder containing all single-page files in their respective sub-folders "
        "will cause the script to perform ILS correction recursively throughout each sub-folder.",
    )
    parser.add_argument(
        "--calibration_id",
        "-c",
        default="CAL",
        help="Identifier in the name of the image that denotes it is from the calibration set. "
        'If not specified, defaults to "CAL".',
    )
    parser.add_argument(
        "--output_path",
        "-o",
        default=None,
        help="Path to output folder at which the corrected images will be stored. If not supplied, "
        "corrected images will be placed into the input directory.",
    )
    parser.add_argument(
        "--no_ils_correct",
        "-i",
        action="store_true",
        help="If selected, ILS correction will not be applied to the images.",
    )
    parser.add_argument(
        "--no_reflectance_correct",
        "-r",
        action="store_true",
        help="If selected, reflectance correction will not be applied to the images.",
    )
    parser.add_argument(
        "--delete_original",
        "-d",
        action="store_true",
        help="Overwrite original 12-bit images with the corrected versions. If selected, corrected "
        "images are renamed to their original names. If not, an extension is added.",
    )
    parser.add_argument(
        "--exiftool_path",
        "-e",
        default=None,
        help="Path to ExifTool executable. ExifTool is required for the conversion; if not passed, "
        "the script will use a bundled ExifTool executable.",
    )
    parser.add_argument(
        "--uint16_output",
        "-u",
        action="store_true",
        help="If selected, scale of output values will be adjusted to 0-65535 and dtype will be "
        "changed to uint16.",
    )

    args = parser.parse_args()

    if not args.exiftool_path:
        if getattr(sys, "frozen", False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app
            # path into variable _MEIPASS'.
            args.exiftool_path = os.path.join(sys._MEIPASS, "exiftool.exe")
        else:
            args.exiftool_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "exiftool",
                "exiftool.exe",
            )
        logger.info(
            "Using bundled executable. Setting ExifTool path to %s", args.exiftool_path
        )

    corrections.correct_images(**vars(args))
