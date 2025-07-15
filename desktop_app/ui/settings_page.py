import streamlit as st
import sqlite3
import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from auth import update_user_password, authenticate_user
from database import get_user_by_id
from datetime import datetime, timedelta
from config import PAGES, DATABASE_NAME

def show_settings_page():
    """Display settings and user profile management page"""
    st.markdown(f'<div class="main-header"><h1>{PAGES["Settings"]["icon"]} {PAGES["Settings"]["title"]}</h1></div>', unsafe_allow_html=True)
    
    st.subheader("🔑 Change Your Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Password", use_container_width=True)
        
        if submitted:
            if not all([current_password, new_password, confirm_password]):
                st.error("Please fill all fields.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            elif len(new_password) < 6:
                st.error("New password must be at least 6 characters long.")
            else:
                # First verify current password
                user = authenticate_user(st.session_state.username, current_password)
                if not user:
                    st.error("❌ Current password is incorrect.")
                else:
                    # Update password
                    success, message = update_user_password(st.session_state.user_id, new_password)
                    if success:
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    
    st.subheader("👤 Your Profile")
    
    user_info = get_user_by_id(st.session_state.user_id)
    if user_info:
        st.text_input("Username", value=user_info['username'], disabled=True)
        st.text_input("Email", value=user_info['email'], disabled=True)
        st.text_input("Account Created", value=pd.to_datetime(user_info['created_at']).strftime('%Y-%m-%d %H:%M'), disabled=True)
    else:
        st.error("Could not retrieve user profile.")
        
    st.markdown("---")
    
    st.subheader("🗑️ Danger Zone")
    
    if st.checkbox("I want to see advanced data management options"):
        st.warning("⚠️ **Warning**: These actions are irreversible. Please be careful.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear Old Sessions (>30 days)", use_container_width=True, type="secondary"):
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    
                    # Get sessions to be deleted for logging
                    cursor.execute("SELECT id FROM upload_session WHERE created_at < ?", (thirty_days_ago,))
                    sessions_to_delete = cursor.fetchall()
                    
                    if sessions_to_delete:
                        # Perform deletion
                        cursor.execute("DELETE FROM upload_session WHERE created_at < ?", (thirty_days_ago,))
                        conn.commit()
                        st.success(f"Successfully cleared {len(sessions_to_delete)} old sessions.")
                    else:
                        st.info("No sessions older than 30 days found.")
                        
                except Exception as e:
                    st.error(f"Failed to clear old sessions: {str(e)}")
                finally:
                    if conn:
                        conn.close()
        
        with col2:
            if st.button("Delete My Account", use_container_width=True, type="primary"):
                st.error("This feature is not yet implemented.")
                # Note: Implementing this would require careful handling of user data and cascading deletes.
                # For example, what happens to the processing sessions associated with the user?
                # A soft delete (marking as inactive) is often a safer approach.

    st.markdown("---")
    st.info("For any issues or feedback, please contact support at support@example.com") 