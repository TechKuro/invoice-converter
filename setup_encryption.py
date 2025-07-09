#!/usr/bin/env python3
"""
Setup script for PDF Invoice Converter Database Encryption
==========================================================

This script helps install SQLCipher dependencies and sets up database encryption.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is supported"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required for database encryption.")
        return False
    return True

def install_dependencies():
    """Install required dependencies for database encryption"""
    print("Installing database encryption dependencies...")
    
    try:
        # Install cryptography library (has pre-built wheels)
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "cryptography>=3.4.0"
        ])
        print("✓ Successfully installed cryptography")
        
        # Install other requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Successfully installed all requirements")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        print("\nTroubleshooting:")
        print("1. Try upgrading pip: python -m pip install --upgrade pip")
        print("2. Try installing cryptography separately: pip install cryptography")
        print("3. Check your internet connection")
        return False

def test_encryption():
    """Test if field-level encryption is working properly"""
    print("\nTesting field-level encryption...")
    
    try:
        # Import the encryption module to trigger initialization
        sys.path.insert(0, str(Path(__file__).parent))
        from desktop_app.encryption import (
            get_field_encryption, 
            encrypt_sensitive_field, 
            decrypt_sensitive_field,
            is_encryption_enabled
        )
        from desktop_app.database import init_database, get_db_connection
        from desktop_app.config import DATABASE_NAME
        
        # Initialize database
        print("Initializing database...")
        init_database()
        
        # Test field encryption
        print("Testing field encryption...")
        test_data = "Test sensitive data 12345"
        
        # Encrypt test data
        encrypted = encrypt_sensitive_field(test_data)
        print(f"✓ Original data: {test_data}")
        print(f"✓ Encrypted data: {encrypted[:50]}..." if len(encrypted) > 50 else f"✓ Encrypted data: {encrypted}")
        
        # Decrypt test data
        decrypted = decrypt_sensitive_field(encrypted)
        print(f"✓ Decrypted data: {decrypted}")
        
        # Verify round-trip encryption
        if decrypted == test_data:
            print("✓ Round-trip encryption test PASSED!")
        else:
            print("✗ Round-trip encryption test FAILED!")
            return False
        
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user")
        result = cursor.fetchone()
        conn.close()
        
        print(f"✓ Database connection test successful!")
        print(f"✓ Database location: desktop_app/{DATABASE_NAME}")
        print(f"✓ Field encryption enabled: {is_encryption_enabled()}")
        print(f"✓ Encryption key file: desktop_app/.field_encryption_key")
        
        return True
        
    except Exception as e:
        print(f"✗ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_security_info():
    """Display security information"""
    print("\n" + "="*60)
    print("FIELD-LEVEL ENCRYPTION SETUP COMPLETE")
    print("="*60)
    print("\nSECURITY INFORMATION:")
    print("- Sensitive database fields are now encrypted with AES-256")
    print("- Encryption key: desktop_app/.field_encryption_key")
    print("- Salt file: desktop_app/.encryption_salt")
    print("- IMPORTANT: Backup both encryption files!")
    print("- If you lose these files, your data cannot be recovered")
    
    print("\nENCRYPTED FIELDS:")
    print("- Invoice numbers, vendors, amounts")
    print("- Line item descriptions and prices")
    print("- File names and paths")
    print("- User email addresses")
    print("- Passwords are separately hashed (not encrypted)")
    
    print("\nFILE SECURITY:")
    print("- Keep encryption files secure and private")
    print("- Consider backing up keys to a secure location")
    print("- Do not share key files or commit to version control")
    print("- Files are automatically added to .gitignore")
    
    print("\nBACKUP RECOMMENDATIONS:")
    print("- Regular backups of database and encryption key files")
    print("- Store backups in encrypted storage")
    print("- Test backup recovery procedures")
    
    print("\nNEXT STEPS:")
    print("- Run your application normally")
    print("- New data will be automatically encrypted")
    print("- Existing data works alongside encrypted data")

def main():
    """Main setup function"""
    print("PDF Invoice Converter - Database Encryption Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed. Please resolve dependency issues and try again.")
        sys.exit(1)
    
    # Test encryption
    if not test_encryption():
        print("\nEncryption test failed. Please check your installation.")
        sys.exit(1)
    
    # Show security information
    show_security_info()
    
    print("\n✓ Database encryption setup completed successfully!")

if __name__ == "__main__":
    main() 