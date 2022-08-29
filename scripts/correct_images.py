"""Radiometric corrections for Sentera sensors."""

import argparse
import logging
from imgcorrect._version import __version__
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

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version='%(prog)s v{version}'.format(version=__version__)
    )

    args = parser.parse_args()

    corrections.correct_images(**vars(args))
