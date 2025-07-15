import streamlit as st
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from database import get_user_stats, get_recent_sessions
from utils import format_status
from config import PAGES

def show_dashboard():
    """Display main dashboard"""
    st.markdown(f'<div class="main-header"><h1>{PAGES["Dashboard"]["icon"]} {PAGES["Dashboard"]["title"]}</h1></div>', unsafe_allow_html=True)
    
    # Stats cards
    stats = get_user_stats(st.session_state.user_id)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['total_sessions']}</h3>
            <p>Total Sessions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['total_files']}</h3>
            <p>Files Processed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{stats['success_rate']:.1f}%</h3>
            <p>Success Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>24/7</h3>
            <p>Available</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent sessions
    st.subheader("🕒 Recent Processing Sessions")
    sessions_df = get_recent_sessions(st.session_state.user_id)
    
    if not sessions_df.empty:
        # Create a copy to avoid modifying the original dataframe
        display_df = sessions_df.copy()
        
        # Format the dataframe for better display - use simple text formatting
        display_df['Status'] = display_df['status'].apply(lambda x: x.capitalize())
        display_df['Created'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['Files'] = display_df['processed_files'].astype(str) + '/' + display_df['total_files'].astype(str)
        
        # Select columns and limit to recent sessions
        final_df = display_df[['session_id', 'Files', 'Status', 'Created']].head(10)
        final_df.columns = ['Session ID', 'Files', 'Status', 'Created']
        
        st.dataframe(final_df, use_container_width=True)
        
        # Action buttons for recent sessions
        if st.button("🔄 Refresh", type="secondary"):
            st.rerun()
    else:
        st.info("No processing sessions yet. Upload some PDFs to get started!")
        if st.button("📤 Upload PDFs", type="primary"):
            # Use query params to switch page
            st.query_params["page"] = "upload"
            st.rerun()



