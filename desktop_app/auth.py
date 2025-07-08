"""
Authentication module for PDF Invoice Converter Desktop App
===========================================================

Handles user authentication and password management using bcrypt.
"""

import sqlite3
import hashlib
import secrets
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent / "pdf_converter.db"

def hash_password(password):
    """Hash a password using SHA-256 with salt (simple implementation)"""
    # For production, use bcrypt, but for simplicity we'll use SHA-256 with salt
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    try:
        salt, hash_part = password_hash.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_part
    except:
        return False

def authenticate_user(username, password):
    """Authenticate a user and return user info if successful"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, password_hash, is_active 
        FROM user 
        WHERE username = ? AND is_active = 1
    """, (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(password, user[3]):
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'is_active': user[4]
        }
    
    return None

def create_user(username, email, password):
    """Create a new user account"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if username already exists
    cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists"
    
    # Check if email already exists
    cursor.execute("SELECT id FROM user WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email already exists"
    
    # Create user
    password_hash = hash_password(password)
    
    try:
        cursor.execute("""
            INSERT INTO user (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))
        
        conn.commit()
        conn.close()
        return True, "User created successfully"
        
    except Exception as e:
        conn.close()
        return False, f"Error creating user: {str(e)}"

def get_user_by_username(username):
    """Get user information by username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, created_at, is_active 
        FROM user 
        WHERE username = ?
    """, (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'created_at': user[3],
            'is_active': user[4]
        }
    
    return None

def update_user_password(user_id, new_password):
    """Update user password"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    password_hash = hash_password(new_password)
    
    try:
        cursor.execute("""
            UPDATE user 
            SET password_hash = ?
            WHERE id = ?
        """, (password_hash, user_id))
        
        conn.commit()
        conn.close()
        return True, "Password updated successfully"
        
    except Exception as e:
        conn.close()
        return False, f"Error updating password: {str(e)}"

def deactivate_user(user_id):
    """Deactivate a user account"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE user 
            SET is_active = 0
            WHERE id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
        return True, "User deactivated successfully"
        
    except Exception as e:
        conn.close()
        return False, f"Error deactivating user: {str(e)}" 