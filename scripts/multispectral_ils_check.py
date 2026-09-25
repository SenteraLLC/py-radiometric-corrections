"""Run multispectral ILS checks for a directory of imagery."""

import argparse

from imgcorrect._version import __version__
from imgcorrect.dataset import multispectral_ils_check

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check calibration panel and flight-image ILS values."
    )
    parser.add_argument(
        "input_path",
        help="Path to the directory containing multispectral images.",
    )
    parser.add_argument(
        "--calibration_id",
        "-c",
        default="CAL",
        help=(
            "Identifier in image names that denotes calibration images. "
            'Defaults to "CAL".'
        ),
    )
    parser.add_argument(
        "--output_file_path",
        "-o",
        default=None,
        help="Optional path for the JSON results file.",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s v{version}".format(version=__version__),
    )

    args = parser.parse_args()
    multispectral_ils_check(**vars(args))
