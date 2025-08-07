cd /d %~dp0
call "%HOMEPATH%\anaconda3\Scripts\activate.bat"
call conda env create -f environment.yml
call "%HOMEPATH%\anaconda3\Scripts\activate.bat" "imgcorrect-venv"
pip install .
"python" "scripts/correct_images_gui.py"