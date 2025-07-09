import streamlit as st
import pandas as pd
from desktop_app.database import get_all_user_sessions
from desktop_app.utils import format_status
from desktop_app.config import PAGES

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
        status_filter = st.selectbox(
            "Filter by status:",
            ['all', 'completed', 'processing', 'failed'],
            format_func=lambda x: x.capitalize()
        )
    
    with col2:
        date_filter = st.date_input("Filter by date (optional):", value=None)
    
    with col3:
        sort_order = st.selectbox(
            "Sort by:",
            ['created_at_desc', 'created_at_asc'],
            format_func=lambda x: 'Newest First' if x == 'created_at_desc' else 'Oldest First'
        )
    
    st.markdown("---")
    
    # Fetch and display sessions
    sessions_df = get_all_user_sessions(st.session_state.user_id, status_filter, date_filter, sort_order)
    
    if not sessions_df.empty:
        # Format for display
        sessions_df['Status'] = sessions_df['status'].apply(format_status)
        sessions_df['Created'] = pd.to_datetime(sessions_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        sessions_df['Files'] = sessions_df['processed_files'].astype(str) + ' / ' + sessions_df['total_files'].astype(str)
        
        display_df = sessions_df[['session_id', 'Files', 'Status', 'Created']]
        display_df.columns = ['Session ID', 'Files Processed', 'Status', 'Date Created']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Pagination (if many sessions)
        # Note: Streamlit doesn't have a native pagination component, this is a simple implementation
        page_size = 10
        total_pages = (len(sessions_df) - 1) // page_size + 1
        
        if total_pages > 1:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            st.dataframe(display_df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)
        else:
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
    else:
        st.info("No sessions found matching your criteria.") 