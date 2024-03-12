# py-radiometric-corrections
Library to perform various corrections on imagery from supported sensors, including Sentera 6X and Sentera Double 4K

### Note - if you just want to run the tool, ImageryCorrector.exe can be downloaded from the most recent tagged Release.
### Skip down to 'Executable Usage' for instructions on the binary executable.

### Installation instructions for usage in Python

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

	>> python scripts\correct_images.py "input_path" --output_path "output_path"
Optional commands:

  --calibration_id "CALIBRATION_ID", -c CALIBRATION_ID
  * Identifier in the name of the image that denotes it is from the calibration set. If not specified, defaults to "CAL".
  
  --output_path OUTPUT_PATH, -o OUTPUT_PATH
  * Path to output folder at which the corrected images will be stored. If not supplied, corrected images will be placed into the input directory.
  
  --no_ils_correct, -i 
  * If selected, ILS correction will not be applied to the images.
  
  --no_reflectance_correct, -r
  * If selected, reflectance correction will not be applied to the images.
  
  --delete_original, -d
  * Overwrite original 12-bit images with the corrected versions. If selected, corrected images are renamed to their original names. If not, an extension is added.
  
  --exiftool_path EXIFTOOL_PATH, -e EXIFTOOL_PATH
  * Path to ExifTool executable. ExifTool is required for the conversion; if not passed, the script will use a bundled ExifTool executable.
  
  --uint16_output, -u   
  * If selected, scale of output values will be adjusted to 0-65535 and dtype will be changed to uint16.

#### Building the Executable
In a Windows 10 x64 environment, rebuild the executable with pyinstaller using this command:

		>> pyinstaller correct_images_onefile.spec

#### Executable Usage
The executable simply wraps the `correct_ils_images.py` script, and exposes the same set of command line options.
To use, navigate to the location of the executable in a terminal window and run 

        >> "Imagery Corrector.exe" -h
        
This will print the command line argument list, as well as help messages explaining each argument.
