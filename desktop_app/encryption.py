"""
Field-level encryption module for PDF Invoice Converter Desktop App
===================================================================

Provides application-level encryption for sensitive database fields using AES-256.
This approach works on all platforms without requiring SQLCipher.
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path
import secrets

# Encryption configuration
ENCRYPTION_KEY_FILE = Path(__file__).parent / ".field_encryption_key"
SALT_FILE = Path(__file__).parent / ".encryption_salt"

class FieldEncryption:
    """Handles field-level encryption for sensitive database data"""
    
    def __init__(self):
        self.cipher = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with key and salt"""
        try:
            # Get or create salt
            salt = self._get_or_create_salt()
            
            # Get or create encryption key
            key_material = self._get_or_create_key()
            
            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_material))
            
            # Initialize Fernet cipher
            self.cipher = Fernet(key)
            
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            self.cipher = None
    
    def _get_or_create_salt(self):
        """Get existing salt or create a new one"""
        if SALT_FILE.exists():
            try:
                with open(SALT_FILE, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading salt file: {e}")
        
        # Generate new salt
        salt = os.urandom(16)
        try:
            with open(SALT_FILE, 'wb') as f:
                f.write(salt)
            
            # Set file permissions (Unix/Linux)
            if os.name != 'nt':
                os.chmod(SALT_FILE, 0o600)
                
            print(f"New encryption salt generated: {SALT_FILE}")
            return salt
            
        except Exception as e:
            print(f"Error saving salt: {e}")
            raise
    
    def _get_or_create_key(self):
        """Get existing key material or create new one"""
        if ENCRYPTION_KEY_FILE.exists():
            try:
                with open(ENCRYPTION_KEY_FILE, 'r') as f:
                    key_hex = f.read().strip()
                return bytes.fromhex(key_hex)
            except Exception as e:
                print(f"Error reading encryption key: {e}")
        
        # Generate new key material
        key_material = secrets.token_bytes(32)  # 256-bit key
        key_hex = key_material.hex()
        
        try:
            with open(ENCRYPTION_KEY_FILE, 'w') as f:
                f.write(key_hex)
            
            # Set file permissions (Unix/Linux)
            if os.name != 'nt':
                os.chmod(ENCRYPTION_KEY_FILE, 0o600)
                
            print(f"New encryption key generated: {ENCRYPTION_KEY_FILE}")
            return key_material
            
        except Exception as e:
            print(f"Error saving encryption key: {e}")
            raise
    
    def encrypt_field(self, data):
        """Encrypt a field value"""
        if not self.cipher:
            return data  # Fallback to unencrypted if encryption fails
        
        if data is None:
            return None
        
        try:
            # Convert to string and encode
            data_str = str(data)
            data_bytes = data_str.encode('utf-8')
            
            # Encrypt and encode as base64 string
            encrypted_bytes = self.cipher.encrypt(data_bytes)
            encrypted_str = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            # Add prefix to identify encrypted fields
            return f"ENC:{encrypted_str}"
            
        except Exception as e:
            print(f"Error encrypting field: {e}")
            return data  # Fallback to original data
    
    def decrypt_field(self, encrypted_data):
        """Decrypt a field value"""
        if not self.cipher:
            return encrypted_data
        
        if encrypted_data is None:
            return None
        
        # Check if data is encrypted (has ENC: prefix)
        if not isinstance(encrypted_data, str) or not encrypted_data.startswith("ENC:"):
            return encrypted_data  # Return as-is if not encrypted
        
        try:
            # Remove prefix and decode
            encrypted_str = encrypted_data[4:]  # Remove "ENC:" prefix
            encrypted_bytes = base64.b64decode(encrypted_str.encode('utf-8'))
            
            # Decrypt
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            return decrypted_str
            
        except Exception as e:
            print(f"Error decrypting field: {e}")
            return encrypted_data  # Return encrypted data if decryption fails
    
    def is_encryption_available(self):
        """Check if encryption is properly initialized"""
        return self.cipher is not None

# Global encryption instance
_field_encryption = None

def get_field_encryption():
    """Get the global field encryption instance"""
    global _field_encryption
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    return _field_encryption

def encrypt_sensitive_field(data):
    """Convenience function to encrypt sensitive data"""
    return get_field_encryption().encrypt_field(data)

def decrypt_sensitive_field(encrypted_data):
    """Convenience function to decrypt sensitive data"""
    return get_field_encryption().decrypt_field(encrypted_data)

def is_encryption_enabled():
    """Check if field encryption is enabled and working"""
    return get_field_encryption().is_encryption_available()

# Fields that should be encrypted (sensitive data)
ENCRYPTED_FIELDS = {
    'invoice_data': ['invoice_number', 'vendor', 'total_amount'],
    'line_item': ['description', 'amount', 'unit_price'],
    'processed_file': ['filename', 'file_path'],
    'user': ['email']  # Keep username unencrypted for login
}

def should_encrypt_field(table_name, field_name):
    """Check if a field should be encrypted"""
    return table_name in ENCRYPTED_FIELDS and field_name in ENCRYPTED_FIELDS[table_name]

def encrypt_row_data(table_name, row_data):
    """Encrypt sensitive fields in a row of data"""
    if not is_encryption_enabled():
        return row_data
    
    encrypted_data = row_data.copy() if isinstance(row_data, dict) else row_data
    
    if table_name in ENCRYPTED_FIELDS:
        for field in ENCRYPTED_FIELDS[table_name]:
            if hasattr(encrypted_data, field) or field in encrypted_data:
                if isinstance(encrypted_data, dict):
                    encrypted_data[field] = encrypt_sensitive_field(encrypted_data[field])
                else:
                    setattr(encrypted_data, field, encrypt_sensitive_field(getattr(encrypted_data, field)))
    
    return encrypted_data

def decrypt_row_data(table_name, row_data):
    """Decrypt sensitive fields in a row of data"""
    if not is_encryption_enabled():
        return row_data
    
    decrypted_data = row_data.copy() if isinstance(row_data, dict) else row_data
    
    if table_name in ENCRYPTED_FIELDS:
        for field in ENCRYPTED_FIELDS[table_name]:
            if hasattr(decrypted_data, field) or field in decrypted_data:
                if isinstance(decrypted_data, dict):
                    decrypted_data[field] = decrypt_sensitive_field(decrypted_data[field])
                else:
                    setattr(decrypted_data, field, decrypt_sensitive_field(getattr(decrypted_data, field)))
    
    return decrypted_data 