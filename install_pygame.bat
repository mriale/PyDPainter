@echo off
get_python_path.py >%TMP%\python_path.txt
<%TMP%\python_path.txt set /p python_path=
echo Installing pygame package...
%python_path% -m pip install pygame --pre
echo Installing numpy package...
%python_path% -m pip install numpy
echo Done.
pause
