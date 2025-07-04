#!/usr/bin/env python3
"""
Run script for PDF Invoice Converter Desktop Application
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the Streamlit desktop application"""
    print("=" * 60)
    print("PDF Invoice Converter - Desktop Application")
    print("=" * 60)
    print("Starting Streamlit application...")
    print("This will open in your default web browser on localhost")
    print("Default login: admin / admin123")
    print("=" * 60)
    print()
    
    # Change to the desktop_app directory
    os.chdir(Path(__file__).parent)
    
    # Run Streamlit with the main.py file
    cmd = [sys.executable, "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.headless=false"]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == "__main__":
    main() 