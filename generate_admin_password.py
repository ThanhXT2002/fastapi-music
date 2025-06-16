#!/usr/bin/env python3
"""
Script to generate secure password hash for admin panel
Usage: python generate_admin_password.py
"""

import bcrypt
import getpass
import os
from pathlib import Path

def generate_password_hash():
    """Generate a secure password hash for admin panel"""
    
    print("🔐 Admin Password Hash Generator")
    print("=" * 40)
    
    # Get password input
    while True:
        password = getpass.getpass("Enter new admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords don't match. Please try again.")
            continue
            
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long.")
            continue
            
        break
    
    # Generate hash
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    hash_string = password_hash.decode('utf-8')
    
    print("\n✅ Password hash generated successfully!")
    print("=" * 40)
    print(f"Hash: {hash_string}")
    
    # Check if .env file exists
    env_file = Path(".env")
    
    print("\n📝 Add this to your .env file:")
    print("=" * 40)
    print(f"ADMIN_PASSWORD_HASH={hash_string}")
    
    # Option to write to .env file
    if env_file.exists():
        write_to_env = input("\n💾 Write to .env file? (y/n): ").lower().strip()
        if write_to_env == 'y':
            with open(env_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# Admin Panel Configuration\n")
                f.write(f"ADMIN_PASSWORD_HASH={hash_string}\n")
            print("✅ Added to .env file!")
    else:
        create_env = input("\n📄 Create .env file? (y/n): ").lower().strip()
        if create_env == 'y':
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("# FastAPI Music API Environment Variables\n\n")
                f.write("# Admin Panel Configuration\n")
                f.write(f"ADMIN_USERNAME=musicadmin\n")
                f.write(f"ADMIN_PASSWORD_HASH={hash_string}\n")
                f.write(f"ADMIN_SECRET_KEY=your-very-secure-admin-secret-key-{os.urandom(16).hex()}\n")
            print("✅ Created .env file with admin configuration!")
    
    print("\n🔄 Restart your FastAPI server to apply changes.")
    
    # Test the hash
    test_password = getpass.getpass("\n🧪 Test password (optional, press Enter to skip): ")
    if test_password:
        if bcrypt.checkpw(test_password.encode('utf-8'), password_hash):
            print("✅ Password verification successful!")
        else:
            print("❌ Password verification failed!")

if __name__ == "__main__":
    try:
        generate_password_hash()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
