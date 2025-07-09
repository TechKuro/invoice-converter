import streamlit as st
import pandas as pd
from desktop_app.database import get_user_stats, get_recent_sessions
from desktop_app.utils import format_status
from desktop_app.config import PAGES

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
        # Format the dataframe for better display
        sessions_df['Status'] = sessions_df['status'].apply(format_status)
        sessions_df['Created'] = pd.to_datetime(sessions_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        sessions_df['Files'] = sessions_df['processed_files'].astype(str) + '/' + sessions_df['total_files'].astype(str)
        
        display_df = sessions_df[['session_id', 'Files', 'Status', 'Created']].head(10)
        display_df.columns = ['Session ID', 'Files', 'Status', 'Created']
        
        st.dataframe(display_df, use_container_width=True)
        
        # Action buttons for recent sessions
        if st.button("🔄 Refresh", type="secondary"):
            st.rerun()
    else:
        st.info("No processing sessions yet. Upload some PDFs to get started!")
        if st.button("📤 Upload PDFs", type="primary"):
            # Use query params to switch page
            st.query_params["page"] = "upload"
            st.rerun()



