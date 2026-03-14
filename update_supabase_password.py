#!/usr/bin/env python3
"""
Update Supabase Password in .env file

This script helps you securely update the DATABASE_URL with your actual Supabase password.
"""
import os
import getpass

def update_supabase_password():
    """Update the DATABASE_URL with actual Supabase password"""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print(".env file not found!")
        return False
    
    # Get password securely
    print("Enter your Supabase database password:")
    password = getpass.getpass("Password: ")
    
    if not password:
        print("Password cannot be empty!")
        return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace placeholder with actual password
    old_url = "postgresql://postgres.svwujphciukwvwsdavqf:[YOUR-PASSWORD]@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
    new_url = f"postgresql://postgres.svwujphciukwvwsdavqf:{password}@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
    
    if "[YOUR-PASSWORD]" not in content:
        print("Password already appears to be set in DATABASE_URL")
        return True
    
    # Update content
    updated_content = content.replace(old_url, new_url)
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.write(updated_content)
    
    print("DATABASE_URL updated successfully!")
    print("Password has been securely stored in .env file")
    
    return True

if __name__ == "__main__":
    print("TruthForge Supabase Password Update")
    print("=" * 40)
    
    if update_supabase_password():
        print("\n✅ Ready to test database connection!")
        print("Run: python test_database.py")
    else:
        print("\n❌ Failed to update password")