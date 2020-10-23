# py-6x-corrections
Library to perform various corrections on native 6X imagery.

### Installation

#### Windows (Conda)
    
1) Download [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for Python3.7

2) Open Anaconda Prompt and clone **py-6x-corrections** with

        >> git clone https://github.com/SenteraLLC/py-6x-corrections.git

3) Open Anaconda Prompt and navigate to **py-6x-corrections/**.  Run

        >> conda env create -f environment.yml
        >> conda activate correct6x-venv
        >> pip install -e .
        
4) This creates an *correct6x-venv* environment that all scripts should be run in and installs the **analyticstest**
   library for the scripts to reference. 
        
If no errors appear, the **correct6x** library should be installed correctly.

### Usage
The imagery correction in this repository can be used via:
* Importing the various library functions defined in the package
* Running the pre-defined scripts with a Python installation of version 3.6 or above
* Running the standalone executable on the command line

#### Executable Usage
The executable simply wraps the `correct_ils_6x_images.py` script, and exposes the same set of command line options.
To use, navigate to the location of the executable in a terminal window and run 

        >> "6X Imagery Corrector.exe" -h
        
This will print the command line argument list, as well as help messages explaining each argument.
