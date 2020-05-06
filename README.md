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
   
#### Linux (Pipenv)

1) If not installed, install **pipenv** with the command

        >> pip install pipenv
        
2) Open a terminal and clone **py-6x-corrections** with

        >> git clone https://github.com/SenteraLLC/py-6x-corrections.git      
        
3) Navigate to **py-6x-corrections/** and run

        >> pipenv install
   
4) Everything should be properly installed within a pipenv environment.  To check it is, run

        >> pipenv run python
        >> import correct6x
        
If no errors appear, the **correct6x** library should be installed correctly