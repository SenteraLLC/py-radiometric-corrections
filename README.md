# Sentera Radiometric Corrections
Tool to perform various corrections on imagery from supported sensors, including Sentera 6X, Sentera Double 4K and DJI Mavic 3 Multispectral.


#### GUI Usage
<img width="602" height="532" alt="image" src="https://github.com/user-attachments/assets/acd53b21-6dfd-4f37-a6e3-269c3bc2a764" />

The Sentera Radiometric Corrections tool will perform corrections on multispectral drone imagery as well as recflectance corrections when a supported Sentera calibration panel is used.

##### Required Inputs
- Input Path: Folder path containing multispectral imagery.  Provide an individual folder of images or a folder containing images from multiple sensors.
- Output Path: Folder path to save the correct images to.

##### Optional Inputs/Parameters
- Reflectance Correction:  Select reflectance correction to perform reflectance corrections using a Sentera calibration panel.  If calibration panel imagery is not detected in the input images, this option will be disabled.
- ILS Correction:  Select ILS correction to perform lighting corrections using a light sensor.  If ILS values are not detected in the input images this option will be disabled.
**Note: If Reflectance and ILS corrections are disabled, images will be corrected for exposure only

##### Advanced Inputs/Parameters
- ExifTool Path: Optionally provide an updated/custom version of exiftool.  If not provided the default version is included in the tool.
- Calibration ID: For Sentera sensors, calibration images are tagged with "CAL".  Optionally provide a different tag if the image names have been modified.  For non-Sentera sensors all images are scanned for calibration panels.
- Use all panel sets(6X):  By default only the best calibration set will be used to perform corrections for Sentera sensors.  Select this option to perform corrections using all available calibration panel captures.
- Delete/Overwrite Original Images: Select this option and set the input and output paths to match to overwrite the original images with the corrected images. Not reccomended as original images cannot be restored.
- Output as uint16(0-65535):  By default corrected images are formated in Float32 with values in reflectance ranging from 0-1.  Selecting this option will output the corrected images in Uint16 with values ranging from 0-65535.  This may be required for certain photogrametry software and corrected images will have a much smaller file size.



#### Building the Executable
In a Windows 10 x64 environment, rebuild the executable with pyinstaller using this command:

		>> pyinstaller correct_images_onefile.spec


