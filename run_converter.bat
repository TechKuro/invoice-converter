@echo off
echo PDF to Excel Converter
echo =====================

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

:: Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt

:: Create pdfs directory if it doesn't exist
if not exist "pdfs" (
    mkdir pdfs
    echo Created 'pdfs' directory
)

:: Check if there are PDFs in the directory
if exist "pdfs\*.pdf" (
    echo Found PDF files, processing...
    python pdf_to_excel_converter.py --input-dir ./pdfs --output-file results.xlsx
    echo.
    echo Check results.xlsx for your extracted line items!
) else (
    echo No PDF files found in 'pdfs' directory
    echo Please add PDF files to the 'pdfs' folder and run this script again
)

echo.
echo Press any key to exit...
pause >nul 