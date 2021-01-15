import click
import logging
import os
import sys

from glob import glob

import imgparse
import correct6x


def _correct_6x_images(input_path,
                       calibration_id,
                       output_path,
                       no_ils_correct,
                       no_reflectance_correct,
                       delete_original,
                       exiftool_path):
    logger = logging.getLogger()

    def _flag_format(flag):
        if flag:
            return "Enabled"
        else:
            return "Disabled"

    if not exiftool_path:
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app
            # path into variable _MEIPASS'.
            exiftool_path = os.path.join(sys._MEIPASS, 'exiftool.exe')
        else:
            exiftool_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         'exiftool',
                                         'exiftool.exe')
        logger.info("Using bundled executable. Setting ExifTool path to %s", exiftool_path)

    logger.info("ILS corrections: %s", _flag_format(not no_ils_correct))
    logger.info("Delete original: %s", _flag_format(delete_original))

    # Read images:
    image_df = correct6x.create_image_df(input_path, output_path)

    # Get image metadata:
    image_df['EXIF'] = image_df.image_path.apply(imgparse.get_exif_data)

    # Get autoexposure correction:
    image_df['autoexposure'] = image_df.apply(lambda row: imgparse.get_autoexposure(row.image_path, row.EXIF), axis=1)

    # Split out calibration images, if present:
    calibration_df, image_df = correct6x.create_cal_df(image_df, calibration_id)

    # Get ILS correction:
    if not no_ils_correct:
        image_df = correct6x.compute_ils_correction(image_df)
    else:
        image_df['ILS_ratio'] = 1

    # Get reflectance correction:
    if not no_reflectance_correct:
        image_df = correct6x.compute_reflectance_correction(image_df, calibration_df)
    else:
        image_df['slope_coefficient'] = 1

    # Apply corrections:
    image_df.apply(lambda row: correct6x.write_image(correct6x.apply_corrections(row), row), axis=1)

    # Copy EXIF:
    copy_command = correct6x.copy_exif(input_path, exiftool_path)
    if copy_command.returncode != 0:
        for file in glob(input_path + '/**/*_f32.tif', recursive=True):
            os.remove(file)
        raise ValueError("Exiftool copy command did not run successfully.")

    if delete_original:
        correct6x.delete_all_originals(image_df)

    if (output_path and (output_path != input_path)) or delete_original:
        correct6x.move_corrected_images(image_df)


@click.group()
@click.option(
    "--log_level",
    type=click.Choice(["DEBUG", "INFO", "WARNING"]),
    default="INFO",
    help="Set logging level for both console and file",
)
def cli(log_level):
    """CLI entrypoint."""
    logging.basicConfig(level=log_level)


@cli.command()
@click.argument("input_path")
@click.option("--calibration_id", default='CAL',
              help='Identifier in the name of the image that denotes it is from the calibration set. '
                   'If not specified, defaults to "CAL".')
@click.option("--output_path",
              help='Path to output folder at which the corrected images will be stored. If not supplied, '
                   'corrected images will be placed into the input directory.')
@click.option("--no_ils_correct",
              default=False,
              is_flag=True,
              help="If selected, ILS correction will not be applied to the images.")
@click.option("--no_reflectance_correct",
              default=False,
              is_flag=True,
              help="If selected, reflectance correction will not be applied to the images.")
@click.option("--delete_original",
              default=False,
              is_flag=True,
              help='Overwrite original 12-bit images with the corrected versions. If selected, corrected '
                   'images are renamed to their original names. If not, an extension is added.')
@click.option("--exiftool_path",
              help="Path to ExifTool executable. ExifTool is required for the conversion; if not passed, "
                   "the script will use a bundled ExifTool executable.")
def run(**kwargs):
    """
    Run image corrections on a folder of 6X imagery.

    Expects a path to single-band, single-page .TIF files taken from a Sentera 6X sensor. Providing a
    file path to the original multi-page images is not currently supported. However,
    specifying a folder containing all single-page files in their respective sub-folders
    will cause the script to perform ILS correction recursively throughout each sub-folder.
    """
    _correct_6x_images(**kwargs)


@cli.command()
def version():
    """Print application version."""
    print(f"correct6x version\t{correct6x.__version__}")


if __name__ == "__main__":
    cli(sys.argv[1:])
