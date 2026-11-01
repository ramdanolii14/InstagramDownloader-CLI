@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
    goto install
)

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=python"
    goto install
)

echo Python 3 tidak ditemukan.
echo Install Python 3.10+ dan aktifkan "Add Python to PATH".
pause
exit /b 1

:install
echo Installing / updating Instagram Archive dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
if errorlevel 1 goto failed
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Installation completed. Start the app with run_windows.bat.
pause
exit /b 0

:failed
echo.
echo Installation failed. Check your Python and internet connection.
pause
exit /b 1
