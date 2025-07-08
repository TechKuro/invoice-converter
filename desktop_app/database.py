"""
Database module for PDF Invoice Converter Desktop App
====================================================

Handles all database operations using SQLite for local storage.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import uuid

# Database file path
DB_PATH = Path(__file__).parent / "pdf_converter.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Upload sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upload_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_files INTEGER DEFAULT 0,
            processed_files INTEGER DEFAULT 0,
            output_file TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    """)
    
    # Processed files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_file (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_session_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            num_pages INTEGER,
            num_tables INTEGER,
            num_line_items INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (upload_session_id) REFERENCES upload_session (id)
        )
    """)
    
    # Invoice data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processed_file_id INTEGER NOT NULL,
            invoice_number TEXT,
            invoice_date DATE,
            vendor TEXT,
            total_amount DECIMAL(10, 2),
            currency TEXT DEFAULT 'USD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (processed_file_id) REFERENCES processed_file (id)
        )
    """)
    
    # Line items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            processed_file_id INTEGER NOT NULL,
            description TEXT,
            quantity DECIMAL(10, 3),
            unit_price DECIMAL(10, 2),
            amount DECIMAL(10, 2),
            vat_rate DECIMAL(5, 2),
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (processed_file_id) REFERENCES processed_file (id)
        )
    """)
    
    # Create default admin user if no users exist
    cursor.execute("SELECT COUNT(*) FROM user")
    if cursor.fetchone()[0] == 0:
        from auth import hash_password
        admin_password_hash = hash_password("admin123")
        cursor.execute("""
            INSERT INTO user (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ("admin", "admin@example.com", admin_password_hash))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Get user statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total sessions
    cursor.execute("SELECT COUNT(*) FROM upload_session WHERE user_id = ?", (user_id,))
    total_sessions = cursor.fetchone()[0]
    
    # Total files
    cursor.execute("""
        SELECT COUNT(*) FROM processed_file pf
        JOIN upload_session us ON pf.upload_session_id = us.id
        WHERE us.user_id = ?
    """, (user_id,))
    total_files = cursor.fetchone()[0]
    
    # Total line items
    cursor.execute("""
        SELECT COUNT(*) FROM line_item li
        JOIN processed_file pf ON li.processed_file_id = pf.id
        JOIN upload_session us ON pf.upload_session_id = us.id
        WHERE us.user_id = ?
    """, (user_id,))
    total_line_items = cursor.fetchone()[0]
    
    # Success rate
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN pf.status = 'completed' THEN 1 END) as completed,
            COUNT(*) as total
        FROM processed_file pf
        JOIN upload_session us ON pf.upload_session_id = us.id
        WHERE us.user_id = ?
    """, (user_id,))
    result = cursor.fetchone()
    success_rate = (result[0] / result[1] * 100) if result[1] > 0 else 0
    
    conn.close()
    
    return {
        'total_sessions': total_sessions,
        'total_files': total_files,
        'total_line_items': total_line_items,
        'success_rate': success_rate
    }

def get_recent_sessions(user_id, limit=10):
    """Get recent upload sessions for user"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT session_id, status, created_at, total_files, processed_files, output_file
        FROM upload_session 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(user_id, limit))
    conn.close()
    return df

def get_all_user_sessions(user_id):
    """Get all sessions for user"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT * FROM upload_session 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def create_upload_session(user_id, total_files):
    """Create a new upload session"""
    session_id = str(uuid.uuid4())
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO upload_session (session_id, user_id, status, created_at, total_files, processed_files)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, 'processing', datetime.now(), total_files, 0))
    
    session_db_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return session_id

def add_processed_file(session_id, filename, file_path, extracted_data):
    """Add a processed file record with extracted data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get session database ID
    cursor.execute("SELECT id FROM upload_session WHERE session_id = ?", (session_id,))
    session_db_id = cursor.fetchone()[0]
    
    # Insert processed file record
    cursor.execute("""
        INSERT INTO processed_file 
        (upload_session_id, filename, file_path, status, num_pages, num_tables, num_line_items, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_db_id,
        filename,
        file_path,
        'completed',
        extracted_data.get('metadata', {}).get('pages', 0),
        len(extracted_data.get('tables', [])),
        len(extracted_data.get('line_items', [])),
        datetime.now()
    ))
    
    file_db_id = cursor.lastrowid
    
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
    
    # Update session processed count
    cursor.execute("""
        UPDATE upload_session 
        SET processed_files = processed_files + 1
        WHERE session_id = ?
    """, (session_id,))
    
    conn.commit()
    conn.close()

def update_session_status(session_id, status, output_file=None):
    """Update session status and optionally set output file"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if output_file:
        cursor.execute("""
            UPDATE upload_session 
            SET status = ?, completed_at = ?, output_file = ?
            WHERE session_id = ?
        """, (status, datetime.now(), output_file, session_id))
    else:
        cursor.execute("""
            UPDATE upload_session 
            SET status = ?, completed_at = ?
            WHERE session_id = ?
        """, (status, datetime.now(), session_id))
    
    conn.commit()
    conn.close()

def get_user_by_id(user_id):
    """Get user information by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, created_at FROM user WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_session_files(session_id):
    """Get all files for a session"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT pf.* FROM processed_file pf
        JOIN upload_session us ON pf.upload_session_id = us.id
        WHERE us.session_id = ?
        ORDER BY pf.processed_at DESC
    """
    df = pd.read_sql_query(query, conn, params=(session_id,))
    conn.close()
    return df

# Model classes for type hints and structure
class User:
    def __init__(self, id, username, email, password_hash, created_at, is_active):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.is_active = is_active

class UploadSession:
    def __init__(self, id, session_id, user_id, status, created_at, completed_at, total_files, processed_files, output_file):
        self.id = id
        self.session_id = session_id
        self.user_id = user_id
        self.status = status
        self.created_at = created_at
        self.completed_at = completed_at
        self.total_files = total_files
        self.processed_files = processed_files
        self.output_file = output_file

class ProcessedFile:
    def __init__(self, id, upload_session_id, filename, file_path, status, error_message, num_pages, num_tables, num_line_items, processed_at):
        self.id = id
        self.upload_session_id = upload_session_id
        self.filename = filename
        self.file_path = file_path
        self.status = status
        self.error_message = error_message
        self.num_pages = num_pages
        self.num_tables = num_tables
        self.num_line_items = num_line_items
        self.processed_at = processed_at

class LineItem:
    def __init__(self, id, processed_file_id, description, quantity, unit_price, amount, vat_rate, source, created_at):
        self.id = id
        self.processed_file_id = processed_file_id
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.amount = amount
        self.vat_rate = vat_rate
        self.source = source
        self.created_at = created_at

class InvoiceData:
    def __init__(self, id, processed_file_id, invoice_number, invoice_date, vendor, total_amount, currency, created_at):
        self.id = id
        self.processed_file_id = processed_file_id
        self.invoice_number = invoice_number
        self.invoice_date = invoice_date
        self.vendor = vendor
        self.total_amount = total_amount
        self.currency = currency
        self.created_at = created_at 