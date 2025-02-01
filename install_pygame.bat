@echo off

REM Try to get path from system and check if zero length
where python >%TMP%\python_path.txt
<%TMP%\python_path.txt set /p python_path=
for /f %%i in ("%python_path%") do set size=%%~zi
if %size% gtr 0 goto install_packages

REM Try to get path from Python
get_python_path.py >%TMP%\python_path.txt
<%TMP%\python_path.txt set /p python_path=

:install_packages
echo Installing packages...
type requirements.txt
%python_path% -m pip install -m pip install -U -r requirements.txt
echo Done.
pause
