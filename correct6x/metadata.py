import subprocess
import logging

logger = logging.getLogger(__name__)

UNNEEDED_TAGS = [
    'ImageWidth',
    'ImageLength',
    'BitsPerSample',
    'Compression',
    'PhotometricInterpretation',
    'StripOffsets',
    'SamplesPerPixel',
    'RowsPerStrip',
    'StripByteCounts',
    'XResolution',
    'YResolution',
    'ResolutionUnit',
    'PlanarConfiguration',
    'Software',
    'ExifTag', # Handled by ExifTool
    'GPSTag' # Handled by ExifTool
]


# TODO: Add TIFF support to imgparse and call `get_exif_data` instead
def load_exif(image_obj_row):
    return image_obj_row.pages[0].tags[34665].value


def copy_exif(source_dir, target_dir, exiftool_path):
    logger.info("Writing EXIF data...")
    copy_command = subprocess.run([exiftool_path,
                                   "-overwrite_original",
                                   "-r",
                                   "-TagsFromFile",
                                   os.path.join(source_dir, "%f.%e"),
                                   target_dir,
                                   "-xmp",
                                   "-exif",
                                   "-ext jpg"],
                                  capture_output=True)

    if copy_command.returncode != 0:
        for file in glob(input_path + '/**/*_f32.tif', recursive=True):
            os.remove(file)
        raise ValueError("Exiftool copy command did not run successfully.")


# TODO: Add this functionality to imgparse and call that instead
def extract_timestamps(image_obj):
    return image_obj.pages[0].tags[306].value


# TODO: Add this functionality to imgparse and call that instead
def form_metadata_list(image_obj_row):
    return [(tag.code, tag.dtype.replace('1', ''), tag.count, tag.value, True)
            for tag in image_obj_row.pages[0].tags
            if tag.name not in UNNEEDED_TAGS]
