import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
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
    
    # Recent sessions with enhanced UX
    st.subheader("🕒 Recent Processing Sessions")
    sessions_df = get_recent_sessions(st.session_state.user_id)
    
    if not sessions_df.empty:
        # Create a copy to avoid modifying the original dataframe
        display_df = sessions_df.copy()
        
        # Format the dataframe for better display
        display_df['Status'] = display_df['status'].apply(lambda x: x.capitalize())
        display_df['Created'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['Files'] = display_df['processed_files'].astype(str) + '/' + display_df['total_files'].astype(str)
        
        # Add action buttons for each session
        st.markdown("**Click on a session below to download the Excel file or view details:**")
        
        # Create interactive session cards instead of a simple dataframe
        for idx, row in display_df.head(10).iterrows():
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
                    col5a, col5b = st.columns(2)
                    
                    with col5a:
                        if row['status'] == 'completed' and pd.notna(row['output_file']) and os.path.exists(row['output_file']):
                            # Download button for completed sessions
                            with open(row['output_file'], 'rb') as file:
                                file_data = file.read()
                                filename = os.path.basename(row['output_file'])
                                st.download_button(
                                    label="📥",
                                    data=file_data,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_{row['session_id']}",
                                    type="primary",
                                    help="Download Excel file"
                                )
                        elif row['status'] == 'completed':
                            st.markdown("❌")
                        else:
                            st.markdown("⏳")
                    
                    with col5b:
                        # Edit session name button
                        if st.button("✏️", key=f"edit_{row['session_id']}", help="Edit session name"):
                            st.session_state[f"editing_{row['session_id']}"] = True
                
                # Edit session name functionality
                if st.session_state.get(f"editing_{row['session_id']}", False):
                    with st.container():
                        st.markdown("**Edit Session Name:**")
                        col_edit1, col_edit2 = st.columns([3, 1])
                        
                        with col_edit1:
                            new_name = st.text_input(
                                "New session name:",
                                value=row.get('session_name', '') if pd.notna(row.get('session_name')) else '',
                                key=f"new_name_{row['session_id']}",
                                placeholder="Enter a friendly name for this session"
                            )
                        
                        with col_edit2:
                            if st.button("💾 Save", key=f"save_{row['session_id']}"):
                                if new_name.strip():
                                    from database import update_session_name
                                    update_session_name(row['session_id'], new_name.strip())
                                    st.success("Session name updated!")
                                    st.session_state[f"editing_{row['session_id']}"] = False
                                    st.rerun()
                                else:
                                    st.error("Please enter a valid name")
                            
                            if st.button("❌ Cancel", key=f"cancel_{row['session_id']}"):
                                st.session_state[f"editing_{row['session_id']}"] = False
                                st.rerun()
                
                # Add a subtle separator
                st.markdown("---")
        
        # Quick actions section
        st.markdown("### 🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Sessions", type="secondary", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("📤 Upload New PDFs", type="primary", use_container_width=True):
                st.query_params["page"] = "upload"
                st.rerun()
        
        with col3:
            if st.button("📁 View All Sessions", type="secondary", use_container_width=True):
                st.query_params["page"] = "sessions"
                st.rerun()
                
    else:
        # Enhanced empty state
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; margin: 1rem 0;">
            <h3>🎯 Ready to Process Your First PDFs?</h3>
            <p style="color: #666; margin: 1rem 0;">Upload your PDF invoices to get started with data extraction and Excel export.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📤 Upload PDFs", type="primary", use_container_width=True):
                st.query_params["page"] = "upload"
                st.rerun()
        
        with col2:
            if st.button("📖 View Help", type="secondary", use_container_width=True):
                st.info("💡 **Tip:** Upload PDF invoices to extract line items, tables, and invoice data into organized Excel files!")



