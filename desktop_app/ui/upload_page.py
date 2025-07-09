import streamlit as st
import pandas as pd
from pathlib import Path
from desktop_app.services import process_uploaded_files
from desktop_app.config import PAGES

def show_upload_page():
    """Display enhanced file upload page"""
    st.markdown(f'<div class="main-header"><h1>{PAGES["Upload PDFs"]["icon"]} {PAGES["Upload PDFs"]["title"]}</h1></div>', unsafe_allow_html=True)

    # Initialize session state for this page if not already present
    if 'processing_session' not in st.session_state:
        st.session_state.processing_session = {
            'uploaded_files': None,
            'has_files': False,
            'is_processing': False,
            'completed': False,
            'results': None,
            'error': None
        }

    # If processing is complete, show results and a button to start over
    if st.session_state.processing_session.get('completed', False):
        show_processing_results()
        if st.button("🔄 Start New Upload", use_container_width=True):
            # Reset the processing session state
            st.session_state.processing_session = {
                'uploaded_files': None,
                'has_files': False,
                'is_processing': False,
                'completed': False,
                'results': None,
                'error': None
            }
            st.rerun()
        return

    # Page introduction
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

                # Define UI elements for progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                verbose_container = st.container()

                # Define callbacks for the service
                def progress_callback(value):
                    progress_bar.progress(value)

                def status_callback(message, is_verbose=False, is_error=False):
                    if is_verbose:
                        if is_error:
                            verbose_container.error(message)
                        else:
                            verbose_container.write(message)
                    else:
                        status_text.text(message)

                try:
                    with st.spinner("Processing files..."):
                        result = process_uploaded_files(
                            current_files, 
                            extract_tables, 
                            extract_text, 
                            verbose_logging,
                            progress_callback=progress_callback,
                            status_callback=status_callback
                        )
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