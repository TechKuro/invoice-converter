@echo off
echo PDF Invoice Converter - Web Application
echo ========================================

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

:: Run the web application
echo.
echo Starting web application...
echo You can access it at: http://localhost:5000
echo Default login: admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo.

cd webapp
python run_webapp.py

echo.
echo Press any key to exit...
pause >nul 