#!/usr/bin/env python3
"""
JWT Key Generator for Asset Validation API
Run this script to generate a new secure JWT secret key
"""

import secrets
import base64

def generate_jwt_key():
    """Generate a cryptographically secure JWT secret key"""
    # Generate 32 random bytes (256 bits)
    key_bytes = secrets.token_bytes(32)
    
    # Encode as base64 for easy storage
    key = base64.b64encode(key_bytes).decode('utf-8')
    
    return key

def main():
    print("🔐 JWT Secret Key Generator")
    print("=" * 40)
    
    key = generate_jwt_key()
    
    print(f"Generated secure JWT key:")
    print(f"SECRET_KEY={key}")
    print()
    print("📋 Instructions:")
    print("1. Copy the key above")
    print("2. Update your .env file:")
    print(f"   SECRET_KEY={key}")
    print("3. Restart your server")
    print()
    print("⚠️  Keep this key secure and never share it publicly!")

if __name__ == "__main__":
    main()