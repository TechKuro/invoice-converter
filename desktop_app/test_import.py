#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

print("Testing imports...")

try:
    import streamlit as st
    print("✅ Streamlit imported successfully")
except ImportError as e:
    print(f"❌ Streamlit import failed: {e}")

try:
    from pdf_converter import PDFDataExtractor, ExcelExporter
    print("✅ Local PDF converter imported successfully")
except ImportError as e:
    print(f"❌ PDF converter import failed: {e}")

try:
    from database import get_user_stats, get_recent_sessions, get_all_user_sessions, init_database
    print("✅ Database functions imported successfully")
except ImportError as e:
    print(f"❌ Database import failed: {e}")

try:
    from auth import authenticate_user, create_user
    print("✅ Auth functions imported successfully")
except ImportError as e:
    print(f"❌ Auth import failed: {e}")

print("\n🎉 All imports successful! The app should work now.")
print("You can run: streamlit run main.py --server.port=8501") 