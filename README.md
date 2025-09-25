# Sentera Radiometric Corrections
Tool to perform various corrections on imagery from supported sensors, including Sentera 6X, Sentera Double 4K and DJI Mavic 3 Multispectral.
#### Installation
To install the Sentera Radiometric Corrections app, download the `Sentera Radiometric Corrections GUI.zip` file from the latest release on the homepage.  After downloading, extract the files and run the executable file.


<p align="center"><img width="802" height="532" alt="image" src="https://github.com/user-attachments/assets/c976fccf-7176-47c5-a4a9-0465d3aba39e" />
</p>

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
- Use All Panel Sets(6X):  By default only the best calibration set will be used to perform corrections for Sentera sensors.  Select this option to perform corrections using all available calibration panel captures.
- Delete/Overwrite Original Images: Select this option and set the input and output paths to match to overwrite the original images with the corrected images. Not reccomended as original images cannot be restored.
- Output as UInt16(0-65535):  By default corrected images are formated in Float32 with values in reflectance ranging from 0-1.  Selecting this option will output the corrected images in Uint16 with values ranging from 0-65535.  This may be required for certain photogrametry software and corrected images will have a much smaller file size.



## Installation instructions for usage/development in Python

#### Windows (Conda)
    
1) Download [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python3.7

2) Open Anaconda Prompt and clone **py-radiometric-corrections** with

        >> git clone https://github.com/SenteraLLC/py-radiometric-corrections.git

3) Open Anaconda Prompt and navigate to **py-radiometric-corrections/**.  Run:

        >> conda env create -f environment.yml
        >> conda activate imgcorrect-venv
        >> pip install .
        
4) This creates an *imgcorrect-venv* environment that all scripts should be run in and installs the **analyticstest**
   library for the scripts to reference. 
        
If no errors appear, the **imgcorrect** library should be installed correctly.

### Usage
The imagery correction in this repository can be used via:
* Importing the various library functions defined in the package
* Running the pre-defined scripts with a Python installation of version 3.6 or above
* Running the standalone executable on the command line

Open Anaconda Prompt and navigate to **py-radiometric-corrections/**.  Run:

        >> conda activate imgcorrect-venv
Get a list of required arguments:	

	>> python scripts\correct_images.py -h 
Run corrections: 

	>> python scripts\correct_images.py "input_path" -o "output_path" **Additional optional commands


Optional commands:

  --calibration_id "CALIBRATION_ID", -c CALIBRATION_ID
  * Identifier in the name of the image that denotes it is from the calibration set. If not specified, defaults to "CAL".
  
  --output_path OUTPUT_PATH, -o OUTPUT_PATH
  * Path to output folder at which the corrected images will be stored. If not supplied, corrected images will be placed into the input directory.
  
  --no_ils_correct, -i 
  * If selected, ILS correction will not be applied to the images.
  
  --no_reflectance_correct, -r
  * If selected, reflectance correction will not be applied to the images.

  --all_panels, -a
  * If selected, reflectance correction will be applied using all panel images.

  --delete_original, -d
  * Overwrite original 12-bit images with the corrected versions. If selected, corrected images are renamed to their original names. If not, an extension is added.
  
  --exiftool_path EXIFTOOL_PATH, -e EXIFTOOL_PATH
  * Path to ExifTool executable. ExifTool is required for the conversion; if not passed, the script will use a bundled ExifTool executable.
  
  --uint16_output, -u   
  * If selected, scale of output values will be adjusted to 0-65535 and dtype will be changed to uint16.


#### Building the Executable
In a Windows 10/11 x64 environment, rebuild the executable with pyinstaller using this command:

		>> pyinstaller correct_images_onefile.spec


