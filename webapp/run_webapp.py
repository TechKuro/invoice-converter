#!/usr/bin/env python3
"""
Simple script to run the PDF Invoice Converter Web Application
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import app

if __name__ == '__main__':
    # Set environment variables for development
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    print("=" * 60)
    print("PDF Invoice Converter - Web Application")
    print("=" * 60)
    print(f"Starting server at: http://localhost:5000")
    print(f"Default login: admin / admin123")
    print("=" * 60)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000) 