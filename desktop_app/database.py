"""
Database module for PDF Invoice Converter Desktop App
====================================================

Handles all database operations with field-level encryption for sensitive data.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import uuid

from .encryption import (
    encrypt_sensitive_field, 
    decrypt_sensitive_field, 
    is_encryption_enabled,
    ENCRYPTED_FIELDS
)
from .config import DATABASE_NAME

# Database file path
DB_PATH = Path(__file__).parent / DATABASE_NAME

def get_db_connection():
    """Create a standard SQLite database connection"""
    return sqlite3.connect(DB_PATH)

def decrypt_result_row(table_name, row_data):
    """Decrypt sensitive fields in a database result row"""
    if not is_encryption_enabled() or not row_data:
        return row_data
    
    # Convert to list for modification
    row_list = list(row_data)
    
    # Get column names for the table (simplified approach)
    if table_name in ENCRYPTED_FIELDS:
        # This is a simplified approach - in a real implementation you'd want
        # to map column positions to field names properly
        for field in ENCRYPTED_FIELDS[table_name]:
            # For now, decrypt specific known columns based on table structure
            if table_name == 'processed_file':
                # filename(1), file_path(2) 
                if field == 'filename' and len(row_list) > 1:
                    row_list[1] = decrypt_sensitive_field(row_list[1])
                elif field == 'file_path' and len(row_list) > 2:
                    row_list[2] = decrypt_sensitive_field(row_list[2])
            elif table_name == 'line_item':
                # description(1), unit_price(3), amount(4)
                if field == 'description' and len(row_list) > 1:
                    row_list[1] = decrypt_sensitive_field(row_list[1])
                elif field == 'unit_price' and len(row_list) > 3:
                    row_list[3] = decrypt_sensitive_field(row_list[3])
                elif field == 'amount' and len(row_list) > 4:
                    row_list[4] = decrypt_sensitive_field(row_list[4])
            elif table_name == 'invoice_data':
                # invoice_number(1), vendor(3), total_amount(4)
                if field == 'invoice_number' and len(row_list) > 1:
                    row_list[1] = decrypt_sensitive_field(row_list[1])
                elif field == 'vendor' and len(row_list) > 3:
                    row_list[3] = decrypt_sensitive_field(row_list[3])
                elif field == 'total_amount' and len(row_list) > 4:
                    row_list[4] = decrypt_sensitive_field(row_list[4])
            elif table_name == 'user':
                # email(2)
                if field == 'email' and len(row_list) > 2:
                    row_list[2] = decrypt_sensitive_field(row_list[2])
    
    return tuple(row_list)

def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
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
        from .auth import hash_password
        admin_password_hash = hash_password("admin123")
        cursor.execute("""
            INSERT INTO user (username, email, password_hash)
            VALUES (?, ?, ?)
        """, ("admin", "admin@example.com", admin_password_hash))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Get user statistics"""
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    
    conn = get_db_connection()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get session database ID
    cursor.execute("SELECT id FROM upload_session WHERE session_id = ?", (session_id,))
    session_db_id = cursor.fetchone()[0]
    
    # Encrypt sensitive file data
    encrypted_filename = encrypt_sensitive_field(filename) if is_encryption_enabled() else filename
    encrypted_file_path = encrypt_sensitive_field(file_path) if is_encryption_enabled() else file_path
    
    # Insert processed file record
    cursor.execute("""
        INSERT INTO processed_file 
        (upload_session_id, filename, file_path, status, num_pages, num_tables, num_line_items, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_db_id,
        encrypted_filename,
        encrypted_file_path,
        'completed',
        extracted_data.get('metadata', {}).get('pages', 0),
        len(extracted_data.get('tables', [])),
        len(extracted_data.get('line_items', [])),
        datetime.now()
    ))
    
    file_db_id = cursor.lastrowid
    
    # Store line items with encryption
    for item in extracted_data.get('line_items', []):
        encrypted_description = encrypt_sensitive_field(item.get('description', '')) if is_encryption_enabled() else item.get('description', '')
        encrypted_amount = encrypt_sensitive_field(item.get('amount')) if is_encryption_enabled() else item.get('amount')
        encrypted_unit_price = encrypt_sensitive_field(item.get('unit_price')) if is_encryption_enabled() else item.get('unit_price')
        
        cursor.execute("""
            INSERT INTO line_item 
            (processed_file_id, description, quantity, unit_price, amount, vat_rate, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_db_id,
            encrypted_description,
            item.get('quantity'),
            encrypted_unit_price,
            encrypted_amount,
            item.get('vat_rate'),
            item.get('source', 'unknown'),
            datetime.now()
        ))
    
    # Store invoice data with encryption
    invoice_data = extracted_data.get('invoice_data', {})
    if invoice_data:
        encrypted_invoice_number = encrypt_sensitive_field(invoice_data.get('invoice_number')) if is_encryption_enabled() else invoice_data.get('invoice_number')
        encrypted_vendor = encrypt_sensitive_field(invoice_data.get('vendor')) if is_encryption_enabled() else invoice_data.get('vendor')
        encrypted_total_amount = encrypt_sensitive_field(invoice_data.get('total_amount')) if is_encryption_enabled() else invoice_data.get('total_amount')
        
        cursor.execute("""
            INSERT INTO invoice_data 
            (processed_file_id, invoice_number, invoice_date, vendor, total_amount, currency, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            file_db_id,
            encrypted_invoice_number,
            invoice_data.get('invoice_date'),
            encrypted_vendor,
            encrypted_total_amount,
            invoice_data.get('currency', 'USD'),
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
    conn = get_db_connection()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, created_at FROM user WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_session_files(session_id):
    """Get all files for a session"""
    conn = get_db_connection()
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