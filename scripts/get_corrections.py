"""Radiometric corrections for Sentera sensors."""

import argparse
import logging
import os

from imgcorrect import corrections, io
from imgcorrect._version import __version__

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
        help="Path to output the radiometric-corrections.csv to.",
    )
    parser.add_argument(
        "--no_ils_correct",
        "-i",
        action="store_true",
        help="If selected, the radiometric-corrections.csv will have unity gains in the ils corrections column",
    )
    parser.add_argument(
        "--no_reflectance_correct",
        "-r",
        action="store_true",
        help="If selected, radiometric-corrections.csv will not use calibration target data in the results",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s v{version}".format(version=__version__),
    )

    args = parser.parse_args()

    corrections_data = corrections.get_corrections(**vars(args))
    io.write_corrections_csv(
        corrections_data, os.path.join(args.output_path, "radiometric-corrections.csv")
    )
