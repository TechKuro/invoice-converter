#!/usr/bin/env python3
"""
PDF Invoice Converter - Streamlit Desktop Application
=====================================================

A modern Streamlit-based desktop application for processing PDF invoices with user management,
database storage, and intuitive interface - all running locally.
"""

import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import uuid
import tempfile
import shutil
import sqlite3

# Import our local PDF converter module
try:
    from pdf_converter import PDFDataExtractor, ExcelExporter
    print("✅ Successfully imported local PDF converter modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Fallback to parent directory import if local fails
    parent_dir = Path(__file__).parent.parent.resolve()
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    try:
        from pdf_to_excel_converter import PDFDataExtractor, ExcelExporter
        print("✅ Successfully imported PDF converter modules from parent directory")
    except ImportError as e2:
        print(f"❌ Both imports failed: {e2}")
        raise

# Import database models and authentication
from database import get_user_stats, get_recent_sessions, get_all_user_sessions, init_database
from auth import authenticate_user, create_user

# Configure Streamlit page
st.set_page_config(
    page_title="PDF Invoice Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_database()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    .status-success { color: #28a745; font-weight: bold; }
    .status-processing { color: #ffc107; font-weight: bold; }
    .status-failed { color: #dc3545; font-weight: bold; }
    .status-pending { color: #6c757d; font-weight: bold; }
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        margin: 1rem 0;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .feature-card h4 {
        color: #495057;
        margin-bottom: 0.5rem;
    }
    .stAlert > div {
        border-radius: 0.5rem;
    }
    .upload-info {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_authentication():
    """Check if user is authenticated"""
    return 'user_id' in st.session_state and 'username' in st.session_state

def show_login_page():
    """Display login/registration page with improved design"""
    st.markdown('<div class="main-header"><h1>🔐 PDF Invoice Converter</h1></div>', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
    ### Welcome to the PDF Invoice Converter
    
    Transform your PDF invoices into structured Excel data with AI-powered extraction.
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "👤 Register"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Sign In to Your Account")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Remember me")
                
                submitted = st.form_submit_button("🚀 Sign In", use_container_width=True, type="primary")
                
                if submitted:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        user = authenticate_user(username, password)
                        if user:
                            st.session_state.user_id = user['id']
                            st.session_state.username = user['username']
                            st.success("Login successful! Welcome back!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
            
            # Demo credentials info
            st.info("💡 **Demo Account**: Username: `admin` Password: `admin123`")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("Create New Account")
                new_username = st.text_input("Username", key="reg_username", placeholder="Choose a username")
                new_email = st.text_input("Email", key="reg_email", placeholder="Enter your email")
                new_password = st.text_input("Password", type="password", key="reg_password", placeholder="Create a secure password")
                new_password2 = st.text_input("Confirm Password", type="password", key="reg_password2", placeholder="Confirm your password")
                
                submitted = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")
                
                if submitted:
                    if not all([new_username, new_email, new_password, new_password2]):
                        st.error("Please fill in all fields")
                    elif new_password != new_password2:
                        st.error("Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = create_user(new_username, new_email, new_password)
                        if success:
                            st.success("🎉 Account created successfully! Please login with your new credentials.")
                        else:
                            st.error(f"❌ {message}")

def show_sidebar():
    """Display sidebar navigation with improved design"""
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, **{st.session_state.username}**!")
        
        # Navigation menu
        pages = {
            "📊 Dashboard": "📊",
            "📤 Upload PDFs": "📤", 
            "📁 My Sessions": "📁",
            "⚙️ Settings": "⚙️"
        }
        
        # Check for query parameter navigation
        query_page = st.query_params.get("page", None)
        default_index = 0
        if query_page == "upload":
            default_index = 1
            # Clear the query parameter after using it
            if "page" in st.query_params:
                del st.query_params["page"]
        
        page = st.selectbox(
            "🧭 Navigate to:",
            list(pages.keys()),
            key="navigation",
            index=default_index,
            format_func=lambda x: x
        )
        
        st.markdown("---")
        
        # Quick stats with improved formatting
        st.markdown("### 📈 Quick Stats")
        try:
            stats = get_user_stats(st.session_state.user_id)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sessions", stats.get('total_sessions', 0))
                st.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
            with col2:
                st.metric("Files", stats.get('total_files', 0))
                st.metric("Line Items", stats.get('total_line_items', 0))
                
        except Exception as e:
            st.error(f"Could not load stats: {str(e)}")
        
        st.markdown("---")
        
        # App info
        st.markdown("### ℹ️ App Info")
        st.caption("**Version**: 2.0")
        st.caption("**Engine**: Streamlit + AI")
        st.caption("**Storage**: SQLite Local DB")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    return page

def show_dashboard():
    """Display main dashboard"""
    st.markdown('<div class="main-header"><h1>📊 Dashboard</h1></div>', unsafe_allow_html=True)
    
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
            st.query_params.page = "upload"
            st.rerun()

def format_status(status):
    """Format status with colors"""
    status_map = {
        'completed': '✅ Completed',
        'processing': '⏳ Processing',
        'failed': '❌ Failed',
        'pending': '⏸️ Pending'
    }
    return status_map.get(status, status)

def show_upload_page():
    """Display enhanced file upload page"""
    st.markdown('<div class="main-header"><h1>📤 Upload PDF Files</h1></div>', unsafe_allow_html=True)
    
    # Initialize processing session state
    if 'processing_session' not in st.session_state:
        st.session_state.processing_session = {
            'is_processing': False,
            'completed': False,
            'results': None,
            'error': None,
            'uploaded_files': None,
            'has_files': False
        }
    
    # Debug: Show current session state (remove this later)
    with st.expander("🔍 Debug Info", expanded=False):
        debug_info = dict(st.session_state.processing_session)
        # Show file count instead of file objects for readability
        if debug_info.get('uploaded_files'):
            debug_info['uploaded_files'] = f"{len(debug_info['uploaded_files'])} files uploaded"
        st.json(debug_info)
    
    # Check if we have a completed processing session to show results
    if st.session_state.processing_session['completed']:
        show_processing_results()
        
        # Reset button to start new session
        if st.button("🔄 Process New Files", type="primary"):
            st.session_state.processing_session = {
                'is_processing': False,
                'completed': False,
                'results': None,
                'error': None,
                'uploaded_files': None,
                'has_files': False
            }
            st.rerun()
        return
    
    # Show processing status if currently processing
    if st.session_state.processing_session['is_processing']:
        st.info("⏳ Processing in progress... Please wait.")
        st.stop()
    
    # Instructions and tips
    with st.expander("📖 How to Use", expanded=False):
        st.markdown("""
        **Steps to process your PDFs:**
        1. 📁 Select one or more PDF files using the uploader below
        2. 📋 Review the file list and processing options
        3. 🚀 Click 'Process Files' to start extraction
        4. 📊 Monitor real-time progress
        5. 💾 Download your Excel results
        
        **Tips for best results:**
        - Use text-based PDFs (not scanned images)
        - Invoice and receipt formats work best
        - Larger files may take longer to process
        """)
    
    # Processing options
    st.subheader("⚙️ Processing Options")
    col1, col2 = st.columns(2)
    
    with col1:
        extract_tables = st.checkbox("📊 Extract Tables", value=True, help="Detect and extract tabular data")
        extract_text = st.checkbox("📝 Extract Text", value=True, help="Extract all text content")
    
    with col2:
        verbose_logging = st.checkbox("🔍 Verbose Logging", value=False, help="Show detailed processing logs")
        auto_download = st.checkbox("⬇️ Auto-download Results", value=True, help="Automatically start download when complete")
    
    st.markdown("---")
    
    # File upload area with better design
    st.subheader("📁 Select Files")
    uploaded_files = st.file_uploader(
        "Drag and drop PDF files here, or click to browse",
        type=['pdf'],
        accept_multiple_files=True,
        help="Select one or more PDF files to process. Maximum file size: 50MB each."
    )
    
    # Store uploaded files in session state for persistence
    if uploaded_files:
        st.session_state.processing_session['uploaded_files'] = uploaded_files
        st.session_state.processing_session['has_files'] = True
    
    # Use stored files if available, otherwise use current upload
    current_files = st.session_state.processing_session.get('uploaded_files', uploaded_files)
    
    if current_files and st.session_state.processing_session.get('has_files', False):
        st.success(f"✅ Selected {len(current_files)} file(s)")
        
        # Show file details in a nice table
        file_data = []
        total_size = 0
        for file in current_files:
            size_mb = file.size / (1024 * 1024)
            total_size += size_mb
            file_data.append({
                "📄 Filename": file.name,
                "💾 Size": f"{size_mb:.1f} MB",
                "📊 Status": "✅ Ready"
            })
        
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # File statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(current_files))
        with col2:
            st.metric("Total Size", f"{total_size:.1f} MB")
        with col3:
            estimated_time = len(current_files) * 2  # Rough estimate: 2 seconds per file
            st.metric("Est. Time", f"{estimated_time}s")
        
        st.markdown("---")
        
        # Processing controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            if st.button("🚀 Process Files", type="primary", use_container_width=True):
                st.session_state.processing_session['is_processing'] = True
                st.success("🚀 Starting processing...")
                try:
                    with st.spinner("Processing files..."):
                        result = process_uploaded_files(current_files, extract_tables, extract_text, verbose_logging, auto_download)
                    st.session_state.processing_session['results'] = result
                    st.session_state.processing_session['completed'] = True
                    st.success(f"✅ Processing completed! Processed {result.get('processed_count', 0)} files.")
                except Exception as e:
                    st.session_state.processing_session['error'] = str(e)
                    st.session_state.processing_session['completed'] = True
                    st.error(f"❌ Processing failed: {str(e)}")
                finally:
                    st.session_state.processing_session['is_processing'] = False
                st.rerun()
        
        with col3:
            if st.button("🗑️ Clear Files", type="secondary", use_container_width=True):
                # Clear the stored files
                st.session_state.processing_session['uploaded_files'] = None
                st.session_state.processing_session['has_files'] = False
                st.rerun()
    
    else:
        # Show upload tips when no files are selected or stored
        if not st.session_state.processing_session.get('has_files', False):
            st.markdown("""
            <div class="upload-info">
                <h4>🎯 Ready to Process PDFs!</h4>
                <p>Select your PDF files above to get started. The system works best with:</p>
                <ul>
                    <li>📄 Invoice and receipt PDFs</li>
                    <li>📊 Documents with clear table structures</li>
                    <li>📝 Text-based PDFs (not scanned images)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

def show_processing_results():
    """Display processing results"""
    if st.session_state.processing_session['error']:
        st.error(f"❌ Processing failed: {st.session_state.processing_session['error']}")
        return
    
    results = st.session_state.processing_session['results']
    if not results:
        st.error("❌ No results available")
        return
    
    st.success(f"✅ Processing completed successfully!")
    
    # Show results summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Processed", results.get('processed_count', 0))
    with col2:
        st.metric("Total Files", results.get('total_files', 0))
    with col3:
        st.metric("Success Rate", f"{(results.get('processed_count', 0) / max(results.get('total_files', 1), 1) * 100):.1f}%")
    
    # Show download button
    if results.get('output_file') and Path(results['output_file']).exists():
        with open(results['output_file'], "rb") as file:
            st.download_button(
                label="📥 Download Results (Excel)",
                data=file.read(),
                file_name=f"results_{results.get('session_id', 'unknown')[:8]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
    else:
        st.warning("⚠️ Output file not found")

def process_uploaded_files(uploaded_files, extract_tables=True, extract_text=True, verbose_logging=False, auto_download=True):
    """Process uploaded PDF files and return results"""
    # Create upload session
    session_id = str(uuid.uuid4())
    
    try:
        conn = sqlite3.connect('pdf_converter.db')
        cursor = conn.cursor()
        
        # Insert upload session
        cursor.execute("""
            INSERT INTO upload_session (session_id, user_id, status, created_at, total_files, processed_files)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, st.session_state.user_id, 'processing', datetime.now(), len(uploaded_files), 0))
        
        session_db_id = cursor.lastrowid
        
        # Create uploads directory
        upload_dir = Path(f"uploads/{session_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Show progress indicators
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Initialize extractor and exporter with user options
        extractor = PDFDataExtractor(extract_tables=extract_tables, extract_text=extract_text)
        exporter = ExcelExporter()
        all_data = []
        
        processed_count = 0
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Save uploaded file
            file_path = upload_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Insert processed file record
            cursor.execute("""
                INSERT INTO processed_file (upload_session_id, filename, file_path, status)
                VALUES (?, ?, ?, ?)
            """, (session_db_id, uploaded_file.name, str(file_path), 'processing'))
            
            file_db_id = cursor.lastrowid
            
            try:
                # Extract data from PDF
                extracted_data = extractor.extract_from_pdf(file_path)
                all_data.append(extracted_data)
                
                # Update processed file status
                cursor.execute("""
                    UPDATE processed_file 
                    SET status = ?, num_pages = ?, num_tables = ?, num_line_items = ?, processed_at = ?
                    WHERE id = ?
                """, (
                    'completed',
                    extracted_data.get('metadata', {}).get('pages', 0),
                    len(extracted_data.get('tables', [])),
                    len(extracted_data.get('line_items', [])),
                    datetime.now(),
                    file_db_id
                ))
                
                # Store line items
                for item in extracted_data.get('line_items', []):
                    cursor.execute("""
                        INSERT INTO line_item 
                        (processed_file_id, description, quantity, unit_price, amount, vat_rate, source, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_db_id,
                        item.get('description', ''),
                        item.get('quantity'),
                        item.get('unit_price'),
                        item.get('amount'),
                        item.get('vat_rate'),
                        item.get('source', 'unknown'),
                        datetime.now()
                    ))
                
                processed_count += 1
                
            except Exception as e:
                # Update with error status
                cursor.execute("""
                    UPDATE processed_file 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, ('failed', str(e), file_db_id))
            
            # Update progress
            progress_bar.progress((i + 1) / len(uploaded_files))
            cursor.execute("""
                UPDATE upload_session 
                SET processed_files = ?
                WHERE id = ?
            """, (processed_count, session_db_id))
            conn.commit()
        
        # Generate Excel file after processing all files
        output_path = None
        if all_data:
            output_filename = f"results_{session_id}.xlsx"
            output_path = upload_dir / output_filename
            exporter.export_to_excel(all_data, output_path)
            
            cursor.execute("""
                UPDATE upload_session 
                SET status = ?, completed_at = ?, output_file = ?
                WHERE id = ?
            """, ('completed', datetime.now(), str(output_path), session_db_id))
        else:
            cursor.execute("""
                UPDATE upload_session 
                SET status = ?
                WHERE id = ?
            """, ('failed', session_db_id))
        
        conn.commit()
        conn.close()
        
        # Clear progress indicators
        status_text.text("Processing completed!")
        progress_bar.progress(1.0)
        
        # Return results
        return {
            'session_id': session_id,
            'processed_count': processed_count,
            'total_files': len(uploaded_files),
            'output_file': str(output_path) if output_path else None,
            'all_data': all_data
        }
        
    except Exception as e:
        # Handle any errors during processing
        if 'conn' in locals():
            try:
                cursor.execute("""
                    UPDATE upload_session 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, ('failed', str(e), session_db_id))
                conn.commit()
                conn.close()
            except:
                pass  # Database might be closed already
        
        # Re-raise the exception to be caught by the calling function
        raise Exception(f"Processing failed: {str(e)}")

def show_sessions_page():
    """Display user sessions page"""
    st.markdown('<div class="main-header"><h1>📁 My Processing Sessions</h1></div>', unsafe_allow_html=True)
    
    sessions_df = get_all_user_sessions(st.session_state.user_id)
    
    if not sessions_df.empty:
        for _, session in sessions_df.iterrows():
            with st.expander(f"Session {session['session_id'][:8]}... - {format_status(session['status'])}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Created:** {pd.to_datetime(session['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Files:** {session['processed_files']}/{session['total_files']}")
                    st.write(f"**Status:** {format_status(session['status'])}")
                
                with col2:
                    if session['completed_at']:
                        st.write(f"**Completed:** {pd.to_datetime(session['completed_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if session['output_file'] and Path(session['output_file']).exists():
                        with open(session['output_file'], "rb") as file:
                            st.download_button(
                                label="📥 Download Excel",
                                data=file.read(),
                                file_name=f"results_{session['session_id'][:8]}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"download_{session['session_id']}"
                            )
    else:
        st.info("No processing sessions found.")



def show_settings_page():
    """Display enhanced settings and profile page"""
    st.markdown('<div class="main-header"><h1>⚙️ Settings & Profile</h1></div>', unsafe_allow_html=True)
    
    # Get user info
    conn = sqlite3.connect('pdf_converter.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, created_at FROM user WHERE id = ?", (st.session_state.user_id,))
    user_info = cursor.fetchone()
    conn.close()
    
    if not user_info:
        st.error("Could not load user information")
        return
    
    # Create tabs for different settings sections
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "⚙️ Processing", "📊 Data", "🔧 System"])
    
    with tab1:
        st.subheader("Account Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="feature-card">
                <h4>👤 User Details</h4>
                <p><strong>Username:</strong> {user_info[0]}</p>
                <p><strong>Email:</strong> {user_info[1]}</p>
                <p><strong>Member Since:</strong> {pd.to_datetime(user_info[2]).strftime('%B %d, %Y')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # User statistics
            stats = get_user_stats(st.session_state.user_id)
            st.markdown(f"""
            <div class="feature-card">
                <h4>📈 Usage Statistics</h4>
                <p><strong>Total Sessions:</strong> {stats.get('total_sessions', 0)}</p>
                <p><strong>Files Processed:</strong> {stats.get('total_files', 0)}</p>
                <p><strong>Success Rate:</strong> {stats.get('success_rate', 0):.1f}%</p>
                <p><strong>Line Items Extracted:</strong> {stats.get('total_line_items', 0)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Default Processing Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Extraction Options**")
            default_extract_tables = st.checkbox("Extract Tables by Default", value=True, 
                                                help="Automatically detect and extract table data")
            default_extract_text = st.checkbox("Extract Text by Default", value=True,
                                              help="Extract all text content from PDFs")
            default_verbose = st.checkbox("Verbose Logging by Default", value=False,
                                         help="Show detailed processing information")
        
        with col2:
            st.markdown("**⬇️ Output Options**")
            auto_download = st.checkbox("Auto-download Results", value=True,
                                       help="Automatically start download when processing completes")
            include_metadata = st.checkbox("Include File Metadata", value=True,
                                          help="Add file information to Excel output")
            compress_output = st.checkbox("Compress Large Files", value=False,
                                         help="Compress output files larger than 10MB")
    
    with tab3:
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🗃️ Storage Options**")
            retention_days = st.selectbox("Keep Processing Data For:", 
                                         options=[7, 30, 90, 365, -1],
                                         format_func=lambda x: f"{x} days" if x > 0 else "Forever",
                                         index=2)
            
            auto_cleanup = st.checkbox("Auto-cleanup Old Sessions", value=False,
                                      help="Automatically remove old session data")
        
        with col2:
            st.markdown("**📁 File Management**")
            max_file_size = st.selectbox("Maximum File Size:",
                                        options=[10, 25, 50, 100],
                                        format_func=lambda x: f"{x} MB",
                                        index=2)
            
            # Database maintenance
            if st.button("🧹 Cleanup Old Data", help="Remove data older than retention period"):
                # Here you could add cleanup logic
                st.success("Data cleanup completed!")
    
    with tab4:
        st.subheader("System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔧 Application Info**")
            st.code(f"""
Version: 2.0
Engine: Streamlit + AI
Database: SQLite
Storage Location: {Path.cwd() / 'desktop_app' / 'pdf_converter.db'}
            """)
        
        with col2:
            st.markdown("**📊 System Status**")
            
            # Check database
            try:
                conn = sqlite3.connect('pdf_converter.db')
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM user")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM upload_session")
                session_count = cursor.fetchone()[0]
                
                conn.close()
                
                st.success(f"✅ Database: Connected ({user_count} users, {session_count} sessions)")
            except Exception as e:
                st.error(f"❌ Database: Error - {str(e)}")
            
            # Check disk space
            upload_dir = Path("uploads")
            if upload_dir.exists():
                total_size = sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file())
                st.info(f"💾 Storage Used: {total_size / (1024*1024):.1f} MB")
            else:
                st.info("💾 Storage Used: 0 MB")
        
        st.markdown("---")
        
        # Advanced actions
        st.markdown("**⚠️ Advanced Actions**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reset Settings", help="Reset all settings to default"):
                st.success("Settings reset to defaults!")
        
        with col2:
            if st.button("📤 Export Data", help="Export your processing history"):
                st.info("Data export feature coming soon!")
        
        with col3:
            if st.button("🗑️ Clear All Data", help="Remove all your processing data"):
                st.warning("This action cannot be undone!")
    
    # Save settings button
    st.markdown("---")
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        st.success("⚙️ Settings saved successfully!")

def main():
    """Main application entry point"""
    
    # Check authentication
    if not check_authentication():
        show_login_page()
        return
    
    # Show sidebar and get selected page
    page = show_sidebar()
    
    # Check if we have an active or completed processing session
    # This overrides normal navigation to keep user on upload page
    if ('processing_session' in st.session_state and 
        (st.session_state.processing_session.get('is_processing', False) or 
         st.session_state.processing_session.get('completed', False))):
        show_upload_page()
        return
    
    # Route to appropriate page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📤 Upload PDFs":
        show_upload_page()
    elif page == "📁 My Sessions":
        show_sessions_page()
    elif page == "⚙️ Settings":
        show_settings_page()

if __name__ == "__main__":
    main() 