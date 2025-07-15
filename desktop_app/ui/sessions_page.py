import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from database import get_all_user_sessions
from utils import format_status
from config import PAGES

def show_sessions_page():
    """Display user's processing sessions"""
    st.markdown(f'<div class="main-header"><h1>{PAGES["My Sessions"]["icon"]} {PAGES["My Sessions"]["title"]}</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
    View your entire history of PDF processing sessions. You can review the status, 
    number of files, and creation date for each session.
    """)
    
    # Session filtering
    st.subheader("🔎 Filter Sessions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter_raw = st.selectbox(
            "Filter by status:",
            ['All', 'completed', 'processing', 'failed'],
            format_func=lambda x: x.capitalize()
        )
        # Convert to the format expected by the database function
        status_filter = None if status_filter_raw == 'All' else status_filter_raw
    
    with col2:
        date_filter_raw = st.selectbox(
            "Filter by date:",
            ['All time', 'Last 7 days', 'Last 30 days', 'Last 90 days']
        )
        # Use the string values expected by the database function
        date_filter = date_filter_raw
    
    with col3:
        sort_order_raw = st.selectbox(
            "Sort by:",
            ['Newest First', 'Oldest First']
        )
        # Convert to the format expected by the database function
        sort_order = 'desc' if sort_order_raw == 'Newest First' else 'asc'
    
    st.markdown("---")
    
    # Fetch and display sessions
    sessions_df = get_all_user_sessions(st.session_state.user_id, status_filter, date_filter, sort_order)
    
    if not sessions_df.empty:
        # Create a copy to avoid modifying the original dataframe
        display_df = sessions_df.copy()
        
        # Format for display - use simple text formatting for dataframes
        display_df['Status'] = display_df['status'].apply(lambda x: x.capitalize())
        display_df['Created'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['Files'] = display_df['processed_files'].astype(str) + ' / ' + display_df['total_files'].astype(str)
        
        # Select and rename columns for display
        final_df = display_df[['session_id', 'Files', 'Status', 'Created']].copy()
        final_df.columns = ['Session ID', 'Files Processed', 'Status', 'Date Created']
        
        # Remove duplicates if any exist
        final_df = final_df.drop_duplicates()
        
        st.dataframe(final_df, use_container_width=True, hide_index=True)
            
    else:
        st.info("No sessions found matching your criteria.") 