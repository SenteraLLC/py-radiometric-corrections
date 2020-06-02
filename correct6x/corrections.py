import imgparse
import logging

import numpy as np

from PIL import Image

logger = logging.getLogger(__name__)


def apply_correction(image_df_row, no_ils_correct, no_reflectance_correct):
    logger.info("Applying correction to image: %s", image_df_row.image_path)

    image_arr = np.asarray(Image.open(image_df_row.image_path)).astype(np.float32)
    image_arr /= image_df_row.AE_correction

    if not no_ils_correct:
        image_arr /= image_df_row.ILS_ratio

    if not no_reflectance_correct:
        image_arr = correct_for_reflectance(image_arr)

