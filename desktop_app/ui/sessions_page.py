import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
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
        
        # Format for display
        display_df['Status'] = display_df['status'].apply(lambda x: x.capitalize())
        display_df['Created'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['Files'] = display_df['processed_files'].astype(str) + ' / ' + display_df['total_files'].astype(str)
        
        st.markdown(f"**Found {len(display_df)} sessions matching your criteria:**")
        
        # Create interactive session cards
        for idx, row in display_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 2])
                
                with col1:
                    # Display session name or fallback to truncated session ID
                    if pd.notna(row.get('session_name')) and row['session_name'].strip():
                        session_display = row['session_name']
                    else:
                        session_display = row['session_id'][:8] + "..."
                    st.markdown(f"**{session_display}**")
                
                with col2:
                    st.markdown(f"📁 {row['Files']}")
                
                with col3:
                    # Status with color coding
                    status_color = "🟢" if row['status'] == 'completed' else "🟡" if row['status'] == 'processing' else "🔴"
                    st.markdown(f"{status_color} {row['Status']}")
                
                with col4:
                    st.markdown(f"📅 {row['Created']}")
                
                with col5:
                    # Action buttons
                    if row['status'] == 'completed' and pd.notna(row['output_file']) and os.path.exists(row['output_file']):
                        # Download button for completed sessions
                        with open(row['output_file'], 'rb') as file:
                            file_data = file.read()
                            filename = os.path.basename(row['output_file'])
                            st.download_button(
                                label="📥 Download",
                                data=file_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"download_sessions_{row['session_id']}",
                                type="primary"
                            )
                    elif row['status'] == 'completed':
                        st.markdown("❌ File not found")
                    else:
                        st.markdown("⏳ Processing...")
                
                # Add a subtle separator
                st.markdown("---")
        
        # Summary statistics
        completed_sessions = len(display_df[display_df['status'] == 'completed'])
        total_files = display_df['total_files'].sum()
        processed_files = display_df['processed_files'].sum()
        
        st.markdown("### 📊 Session Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Completed Sessions", completed_sessions)
        with col2:
            st.metric("Total Files", total_files)
        with col3:
            st.metric("Successfully Processed", processed_files)
            
    else:
        st.info("No sessions found matching your criteria.") 