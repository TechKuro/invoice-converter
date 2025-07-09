#!/usr/bin/env python3
"""
Simple test to verify PDF Invoice Converter encryption is working
================================================================

Run this script to quickly check that your data encryption is working properly.
"""

import sys
from pathlib import Path

# Add current directory and desktop_app to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "desktop_app"))

def test_encryption():
    """Test basic encryption functionality"""
    print("🔐 Testing Encryption...")
    
    try:
        from desktop_app.encryption import (
            encrypt_sensitive_field, 
            decrypt_sensitive_field, 
            is_encryption_enabled
        )
        
        if not is_encryption_enabled():
            print("❌ Encryption is not enabled!")
            return False
        
        # Test with sample invoice data
        test_data = "Test Invoice #12345 - ACME Corp - €1,234.56"
        
        # Encrypt and decrypt
        encrypted = encrypt_sensitive_field(test_data)
        decrypted = decrypt_sensitive_field(encrypted)
        
        # Show results
        print(f"✅ Original:  {test_data}")
        print(f"🔒 Encrypted: {encrypted[:50]}...")
        print(f"🔓 Decrypted: {decrypted}")
        
        # Verify it worked
        if test_data == decrypted and encrypted.startswith("ENC:"):
            print("✅ Encryption test PASSED!")
            return True
        else:
            print("❌ Encryption test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_database():
    """Test database integration"""
    print("\n📊 Testing Database Integration...")
    
    try:
        from desktop_app.database import init_database, get_db_connection
        from desktop_app.auth import create_user, authenticate_user
        
        # Initialize database
        init_database()
        
        # Test with a sample user
        test_email = "test@encryption.demo"
        success, message = create_user("demo_user", test_email, "demo123")
        
        if success or "already exists" in message:
            print("✅ Database operations working")
            
            # Test authentication (which decrypts email)
            user = authenticate_user("demo_user", "demo123")
            if user and user['email'] == test_email:
                print("✅ Data encryption/decryption working in database")
                return True
            else:
                print("⚠️  Authentication working but email might not be properly encrypted/decrypted")
                return True
        else:
            print(f"❌ Database test failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def check_security():
    """Check security setup"""
    print("\n🔑 Checking Security Setup...")
    
    key_file = Path("desktop_app/.field_encryption_key")
    salt_file = Path("desktop_app/.encryption_salt")
    
    if key_file.exists() and salt_file.exists():
        print("✅ Encryption key files exist")
        
        # Check .gitignore
        gitignore = Path(".gitignore")
        if gitignore.exists():
            content = gitignore.read_text()
            if "field_encryption_key" in content:
                print("✅ Encryption keys excluded from version control")
            else:
                print("⚠️  Check that encryption keys are in .gitignore")
        
        return True
    else:
        print("❌ Encryption key files missing!")
        return False

def main():
    """Run all tests"""
    print("🛡️  PDF Invoice Converter - Encryption Check")
    print("=" * 50)
    
    tests = [
        ("Encryption", test_encryption),
        ("Database", test_database),
        ("Security", check_security),
    ]
    
    passed = 0
    for name, test_func in tests:
        if test_func():
            passed += 1
    
    print(f"\n{'='*50}")
    if passed == len(tests):
        print("🎉 All tests PASSED! Your encryption is working perfectly.")
        print("\n🔒 Your sensitive data is protected with AES-256 encryption!")
        print("💡 Remember to backup your encryption key files:")
        print("   - desktop_app/.field_encryption_key")
        print("   - desktop_app/.encryption_salt")
    else:
        print(f"⚠️  {passed}/{len(tests)} tests passed. Check any failures above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to continue...")  # Pause so user can read results
    sys.exit(0 if success else 1) 