@echo off
echo PDF Invoice Converter - Desktop Application
echo ===========================================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

:: Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Run the desktop application
echo.
echo Starting desktop application...
echo This will open in your default web browser
echo Default login: admin / admin123
echo.
echo Press Ctrl+C to stop the application
echo.

cd desktop_app
python run_app.py

echo.
echo Press any key to exit...
pause >nul 