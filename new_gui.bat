cd /d %~dp0
call "%HOMEPATH%\anaconda3\Scripts\activate.bat"
call "%HOMEPATH%\anaconda3\Scripts\activate.bat" "imgcorrect-venv"
"python" "scripts/correct_images_gui.py"