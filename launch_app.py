#!/usr/bin/env python3
"""
PDF Invoice Converter - Simple Launcher
=======================================

A simple launcher script for the Streamlit desktop application.
This script ensures everything is set up correctly and launches the app.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the PDF Invoice Converter Streamlit app"""
    
    print("=" * 60)
    print("🚀 PDF Invoice Converter - Streamlit Desktop App")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print("Current version:", sys.version)
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("✅ Python version:", sys.version.split()[0])
    
    # Check if we're in the right directory
    if not Path("desktop_app").exists():
        print("❌ Error: desktop_app directory not found")
        print("Please run this script from the project root directory")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("✅ Project structure: OK")
    
    # Install dependencies if needed
    print("🔧 Checking dependencies...")
    try:
        import streamlit
        import pandas
        import pdfplumber
        import openpyxl
        print("✅ All dependencies installed")
    except ImportError as e:
        print(f"⚠️  Installing missing dependency: {e.name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    
    # Set up environment for Python imports
    project_root = Path(".").resolve()
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Change to desktop_app directory
    os.chdir("desktop_app")
    
    print()
    print("🌟 Starting Streamlit application...")
    print(f"📍 URL: http://localhost:8502")
    print(f"🔑 Default login: admin / admin123")
    print()
    print("💡 The app will open in your default web browser")
    print("💡 Press Ctrl+C in this terminal to stop the app")
    print("=" * 60)
    print()
    
    # Launch Streamlit with proper environment on port 8502 to avoid conflicts
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "main.py", 
               "--server.port=8502", "--server.headless=false"]
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 