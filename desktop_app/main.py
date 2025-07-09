#!/usr/bin/env python3
"""
PDF Invoice Converter - Streamlit Desktop Application
=====================================================

A modern Streamlit-based desktop application for processing PDF invoices with user management,
database storage, and intuitive interface - all running locally.
"""

import streamlit as st
import sys
from pathlib import Path

# Import our local PDF converter module
from .pdf_converter import PDFDataExtractor, ExcelExporter

# Import authentication and database initialization
from .auth import authenticate_user, create_user
from .database import init_database, get_user_stats

# Import utility functions
from .utils import load_css, check_authentication

# Import page-rendering functions
from .ui.dashboard_page import show_dashboard
from .ui.upload_page import show_upload_page
from .ui.sessions_page import show_sessions_page
from .ui.settings_page import show_settings_page

# Import configuration
from .config import APP_TITLE, PAGE_ICON, PAGES, APP_VERSION

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Main Application Logic ---

def show_login_page():
    """Display login/registration page."""
    st.markdown('<div class="main-header"><h1>🔐 PDF Invoice Converter</h1></div>', unsafe_allow_html=True)
    
    st.markdown("### Welcome! Please log in or register to continue.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "👤 Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("🚀 Sign In", use_container_width=True)
                
                if submitted:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user_id = user['id']
                        st.session_state.username = user['username']
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", key="reg_username")
                new_email = st.text_input("Email", key="reg_email")
                new_password = st.text_input("Password", type="password", key="reg_password")
                new_password2 = st.text_input("Confirm Password", type="password", key="reg_password2")
                
                submitted = st.form_submit_button("✨ Create Account", use_container_width=True)
                
                if submitted:
                    if new_password != new_password2:
                        st.error("Passwords don't match")
                    else:
                        success, message = create_user(new_username, new_email, new_password)
                        if success:
                            st.success("Account created successfully! Please login.")
                        else:
                            st.error(message)

def show_sidebar():
    """Display the sidebar and return the selected page."""
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
        
        page_name = st.selectbox("Navigate to:", list(PAGES.keys()), format_func=lambda name: f"{PAGES[name]['icon']} {name}")
        
        st.markdown("---")
        
        # Quick stats
        stats = get_user_stats(st.session_state.user_id)
        st.metric("Total Sessions", stats.get('total_sessions', 0))
        st.metric("Total Files Processed", stats.get('total_files', 0))
        
        st.markdown("---")

        st.caption(f"Version: {APP_VERSION}")
        
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state.user_id
            del st.session_state.username
            st.rerun()
            
    # A dictionary to map page names to their functions
    page_functions = {
        "Dashboard": show_dashboard,
        "Upload PDFs": show_upload_page,
        "My Sessions": show_sessions_page,
        "Settings": show_settings_page,
    }
            
    return page_functions[page_name]

def main():
    """Main function to run the app."""
    load_css("desktop_app/style.css")
    init_database()

    if not check_authentication():
        show_login_page()
    else:
        page_function = show_sidebar()
        page_function()

if __name__ == "__main__":
    main() 