@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py
    if errorlevel 1 pause
    exit /b
)

where python >nul 2>nul
if %errorlevel%==0 (
    python app.py
    if errorlevel 1 pause
    exit /b
)

echo Python 3 tidak ditemukan.
echo Install Python 3.10+ dan aktifkan "Add Python to PATH".
pause
exit /b 1
