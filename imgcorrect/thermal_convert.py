import os
import numpy as np
import imageio
import shutil
import exifread
import sys

## 12-bit support requires pip install imagecodecs


def convert_thermal(input_path, output_path, exiftool_path):

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    images = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f))]

    # copy image to output location
    for image in images:
        output_image_path = os.path.join(output_path, image)
        print('output_path: {}'.format(output_image_path))
        shutil.copy(os.path.join(input_path, image), output_image_path)

        # open image in output folder and get image pixel data
        image_io_reader = imageio.get_reader(output_image_path, format='tif')
        image_io = image_io_reader.get_data(0)

        # multiply pixel data by scale coefficient and write to file
        image_io_corrected = (image_io/100-273.15).astype(np.float32)

        image_io_writer = imageio.get_writer(output_image_path, format='tif')
        image_io_writer.append_data(image_io_corrected)

        image_io_reader.close()
        image_io_writer.close()

        # copy exif and xmp data from input image to corrected image
        print('copying exif data')
        os.system('{} -overwrite_original -TagsFromFile "{}" "-xmp" "-exif" "-all"  "{}"'.format(exiftool_path, os.path.join(input_path, image), output_image_path))

        print('editing band info')
        os.system(
            '{} -config "C:\Sentera_Tools\py-radiometric-corrections\cfg\exiftool.cfg" -overwrite_original "-xmp-Camera:BandName=LWIR" "-xmp-Camera:CentralWavelength=11000" "-xmp-Camera:WavelengthFWHM=6000" "{}" '.format(
                exiftool_path,
                output_image_path)
            )

    output_files = [f for f in os.listdir(output_path) if os.path.isfile(os.path.join(output_path, f))]
    for file in output_files:
        if file.endswith('original'):
            try:
                os.remove(os.path.join(output_path, file))
                print('additional file deleted')
            except:
                print('file delete failed')
