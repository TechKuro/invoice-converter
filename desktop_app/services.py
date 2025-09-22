from pathlib import Path
import uuid
from datetime import datetime
import sqlite3
from pdf_converter import PDFDataExtractor, ExcelExporter
from config import DATABASE_NAME

def process_uploaded_files(uploaded_files,
                           user_id,
                           session_name=None,
                           extract_tables=True,
                           extract_text=True,
                           verbose_logging=False,
                           progress_callback=None,
                           status_callback=None):
    """
    Process uploaded PDF files and return results.
    This function is now decoupled from the Streamlit UI.
    """
    session_id = str(uuid.uuid4())
    
    # Generate session name from first file if not provided
    if not session_name and uploaded_files:
        first_filename = uploaded_files[0].name
        # Remove extension and clean up the name
        session_name = Path(first_filename).stem
        # Limit length and clean up
        session_name = session_name[:50].replace('_', ' ').replace('-', ' ')
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO upload_session (session_id, session_name, user_id, status, created_at, total_files, processed_files)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, session_name, user_id, 'processing', datetime.now(), len(uploaded_files), 0))
        
        session_db_id = cursor.lastrowid
        
        upload_dir = Path(f"uploads/{session_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        extractor = PDFDataExtractor(extract_tables=extract_tables, extract_text=extract_text)
        exporter = ExcelExporter()
        all_data = []
        processed_count = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            if status_callback:
                status_callback(f"Processing {uploaded_file.name}...")
            
            file_path = upload_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            cursor.execute("""
                INSERT INTO processed_file (upload_session_id, filename, file_path, status)
                VALUES (?, ?, ?, ?)
            """, (session_db_id, uploaded_file.name, str(file_path), 'processing'))
            
            file_db_id = cursor.lastrowid
            
            try:
                data = extractor.extract_from_pdf(file_path)
                # The extract_from_pdf method returns a dict, we need to convert it to a list
                if data:
                    all_data.append(data)
                
                cursor.execute("UPDATE processed_file SET status = ? WHERE id = ?", ('completed', file_db_id))
                processed_count += 1
                
                if verbose_logging and status_callback:
                    status_callback(f"✅ Extracted data from {uploaded_file.name}", is_verbose=True)
                    
            except Exception as e:
                cursor.execute("UPDATE processed_file SET status = ? WHERE id = ?", ('failed', file_db_id))
                if verbose_logging and status_callback:
                    status_callback(f"❌ Failed to extract data from {uploaded_file.name}: {e}", is_verbose=True, is_error=True)
            
            if progress_callback:
                progress_callback((i + 1) / len(uploaded_files))
        
        if status_callback:
            status_callback("Processing complete! Generating Excel file...")
        
        output_filename = f"results_{session_id[:8]}.xlsx"
        output_file_path = upload_dir / output_filename
        exporter.export_to_excel(all_data, output_file_path)
        output_file = str(output_file_path)
        
        cursor.execute("""
            UPDATE upload_session 
            SET status = ?, processed_files = ?, output_file = ?
            WHERE id = ?
        """, ('completed', processed_count, output_file, session_db_id))
        
        conn.commit()
        
        return {
            'session_id': session_id,
            'total_files': len(uploaded_files),
            'processed_count': processed_count,
            'output_file': output_file,
            'data': all_data
        }

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            
        if 'session_db_id' in locals():
            cursor.execute("UPDATE upload_session SET status = ? WHERE id = ?", ('failed', session_db_id))
            conn.commit()
        
        raise e
        
    finally:
        if 'conn' in locals() and conn:
            conn.close() 