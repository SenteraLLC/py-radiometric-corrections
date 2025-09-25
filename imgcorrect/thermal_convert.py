"""Processing for 6x thermal imagery."""

import logging
import os
import shutil
import subprocess
import tempfile

import imageio
import numpy as np
from tqdm import tqdm

from imgcorrect.io import TqdmToLogger

## 12-bit support requires pip install imagecodecs

logger = logging.getLogger(__name__)


def convert_thermal(input_path, output_path, exiftool_path):
    """Convert 6x thermal."""
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    images = [
        f
        for f in os.listdir(input_path)
        if os.path.isfile(os.path.join(input_path, f)) and f.endswith(".tif")
    ]

    logger.info("Converting LWIR images from CentiKelvin(uint16) to Celsius(float32)")
    with tempfile.TemporaryDirectory() as temp_dir:
        # copy image to output location
        for image in tqdm(images, unit="image", file=TqdmToLogger(logger)):

            if "CAL" not in image:
                # Copy image to temporary directory
                output_image_path = os.path.join(temp_dir, image)
                shutil.copy(os.path.join(input_path, image), output_image_path)

                # open image in output folder and get image pixel data
                image_io_reader = imageio.get_reader(output_image_path, format="tif")
                image_io = image_io_reader.get_data(0)

                # multiply pixel data by scale coefficient and write to file
                image_io_corrected = (image_io / 100 - 273.15).astype(np.float32)

                image_io_writer = imageio.get_writer(output_image_path, format="tif")
                image_io_writer.append_data(image_io_corrected)

                image_io_reader.close()
                image_io_writer.close()

                # copy exif and xmp data from input image to corrected image
                command = [
                    exiftool_path,
                    "-config",
                    "cfg/exiftool.cfg",
                    "-overwrite_original",
                    "-TagsFromFile",
                    os.path.join(input_path, image),
                    "-xmp",
                    "-exif",
                    "-all",
                    output_image_path,
                ]
                results = subprocess.run(
                    command,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if results.returncode != 0:
                    raise ValueError("Exiftool command did not run successfully.")

                # Copy output from temp directory to output directory
                shutil.copy(output_image_path, os.path.join(output_path, image))

                output_files = [
                    f
                    for f in os.listdir(output_path)
                    if os.path.isfile(os.path.join(output_path, f))
                ]
                for file in output_files:
                    if file.endswith("original"):
                        try:
                            os.remove(os.path.join(output_path, file))
                            logger.info("additional file deleted")
                        except Exception as e:
                            logger.error(f"File delete failed with error {e}")
