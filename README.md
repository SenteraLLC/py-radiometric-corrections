# py-radiometric-corrections
Library to perform various corrections on imagery from supported sensors.

### Installation

#### Windows (Conda)
    
1) Download [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python3.7

2) Open Anaconda Prompt and clone **py-radiometric-corrections** with

        >> git clone https://github.com/SenteraLLC/py-radiometric-corrections.git

3) Open Anaconda Prompt and navigate to **py-radiometric-corrections/**.  Run

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

#### Executable Usage
The executable simply wraps the `correct_ils_images.py` script, and exposes the same set of command line options.
To use, navigate to the location of the executable in a terminal window and run 

        >> "Imagery Corrector.exe" -h
        
This will print the command line argument list, as well as help messages explaining each argument.
