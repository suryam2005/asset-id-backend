#!/usr/bin/env python3
"""
Backend Verification Script
Verifies that the backend is properly configured and ready for hosting
"""

import os
from dotenv import load_dotenv

def main():
    print("🚀 Backend Verification")
    print("=" * 30)
    
    # Load environment
    load_dotenv()
    
    # Check JWT key
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and len(secret_key) >= 32:
        print("✅ Secure JWT key configured")
    else:
        print("❌ JWT key missing or too short")
        return False
    
    # Check imports
    try:
        from main import app
        print("✅ Main app imports successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check Supabase config
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if supabase_url and supabase_key:
        print("✅ Supabase configuration found")
    else:
        print("❌ Supabase configuration missing")
        return False
    
    print()
    print("🎉 Backend is ready for hosting!")
    print("📋 Next steps:")
    print("   1. Run: python production.py")
    print("   2. Test: python test_api.py")
    print("   3. Access: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    main()