"""This script processes images in a specified input folder, detects panel bounding boxes using the `extract_panel_bounds` function, and saves the
results with bounding boxes drawn in an output folder.
The script is designed to handle images from supported sensors and can process multiple images organized in sub-folders.
"""

import argparse
import os

import cv2 as cv
import numpy as np
from PIL import Image

from imgcorrect.detect_panel import convert_to_type, extract_panel_bounds


def create_panel_bounding_box_image(input_folder_path, output_folder_path):
    """Process all images in the input folder, detect the panel bounding box, and save the results with bounding boxes drawn."""

    os.makedirs(output_folder_path, exist_ok=True)
    input_folders = [
        os.path.join(input_folder_path, f)
        for f in os.listdir(input_folder_path)
        if os.path.isdir(os.path.join(input_folder_path, f))
    ]

    for folder in input_folders:
        os.makedirs(
            os.path.join(output_folder_path, os.path.basename(folder)), exist_ok=True
        )
        input_images = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".tif", ".tiff"))
        ]

        for image in input_images:
            # Load and process your image
            image_array = np.asarray(Image.open(image))
            image_8bit = convert_to_type(image_array, image_array.max(), np.uint8)

            # Get the bounding box
            panel = extract_panel_bounds(image_8bit)

            if panel is not None:
                # Create a color version for visualization if grayscale
                if len(image_8bit.shape) == 2:
                    vis_image = cv.cvtColor(image_8bit, cv.COLOR_GRAY2BGR)
                else:
                    vis_image = image_8bit.copy()

                # Draw the bounding box
                cv.rectangle(
                    vis_image, panel.top_left, panel.bottom_right, (0, 255, 0), 2
                )

                # Optionally add text showing the Aruco ID
                cv.putText(
                    vis_image,
                    f"ID: {panel.aruco_id}",
                    (panel.top_left[0], panel.top_left[1] - 10),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

                # Save the result
                output_path = os.path.join(
                    output_folder_path,
                    os.path.basename(folder),
                    os.path.basename(image),
                )
                cv.imwrite(output_path, vis_image)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_folder_path",
        help="Path to image files taken from supported sensors. Providing a "
        "file path to the original multi-page images is not currently supported. However, "
        "specifying a folder containing all single-page files in their respective sub-folders "
        "will cause the script to perform ILS correction recursively throughout each sub-folder.",
    )
    parser.add_argument(
        "output_folder_path",
        help="Path to output the panel bounding box images.",
    )

    args = parser.parse_args()
    create_panel_bounding_box_image(**vars(args))
