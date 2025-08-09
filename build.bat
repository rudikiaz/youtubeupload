@echo off
echo ========================================
echo YouTube Video Uploader - Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Installing/upgrading PyInstaller...
python -m pip install --user --upgrade pyinstaller>=5.10.0

echo.
echo Running build script...
python build_executable.py

echo.
echo Build process completed!
pause