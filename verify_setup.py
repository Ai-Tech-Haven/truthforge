"""
Verification script to check if all API Keys components are properly installed
"""
import sys
import os


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False


def check_imports():
    """Check if all required modules can be imported"""
    print("\nChecking Python imports...")
    
    imports_to_check = [
        ("database.database", "Database module"),
        ("database.api_keys", "API Keys model"),
        ("utils.api_keys", "API Keys utilities"),
        ("api.auth", "Authentication module"),
    ]
    
    all_ok = True
    for module_name, description in imports_to_check:
        try:
            __import__(module_name)
            print(f"✅ {description}: {module_name}")
        except ImportError as e:
            print(f"❌ {description} IMPORT ERROR: {e}")
            all_ok = False
    
    return all_ok


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("TruthForge API Keys Setup Verification")
    print("=" * 60)
    
    all_checks_passed = True
    
    # Check Python files
    print("\nChecking Python files...")
    files_to_check = [
        ("database/api_keys.py", "API Keys model"),
        ("utils/__init__.py", "Utils package init"),
        ("utils/api_keys.py", "API Keys utilities"),
        ("api/auth.py", "Authentication module"),
        ("init_database.py", "Database initialization"),
        ("test_api_keys.py", "Test suite"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # Check batch files
    print("\nChecking batch files...")
    batch_files = [
        ("init_database.bat", "Database init batch"),
        ("test_api_keys.bat", "Test batch"),
        ("RUN_API_KEYS_SETUP.bat", "Complete setup batch"),
    ]
    
    for filepath, description in batch_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # Check documentation
    print("\nChecking documentation...")
    docs = [
        ("API_KEYS_README.md", "Main README"),
        ("QUICK_START_API_KEYS.md", "Quick start guide"),
        ("API_KEYS_PORT_FILTER_IMPLEMENTATION.md", "Full implementation guide"),
        ("IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
    ]
    
    for filepath, description in docs:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # Check imports
    if not check_imports():
        all_checks_passed = False
    
    # Check frontend file
    print("\nChecking frontend files...")
    frontend_file = "truthforge_frontend/truthforge-logistics-verified-main/src/pages/DashboardPage.tsx"
    if not check_file_exists(frontend_file, "Dashboard with port filter"):
        all_checks_passed = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\nYou're ready to go! Next steps:")
        print("1. Run: RUN_API_KEYS_SETUP.bat")
        print("2. Or run: python test_api_keys.py")
        print("3. Start server: python main.py")
        print("4. Read: QUICK_START_API_KEYS.md")
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above and ensure all files are present.")
        sys.exit(1)
    
    print("=" * 60)


if __name__ == "__main__":
    main()
