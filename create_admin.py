#!/usr/bin/env python3
"""
Script to create an admin user
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def create_admin_user():
    """Create an admin user"""
    
    admin_user = {
        "username": "admin",
        "email": "admin@company.com",
        "password": "admin123",
        "role": "admin"
    }
    
    print("Creating admin user...")
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=admin_user)
        if response.status_code == 200:
            print("✓ Admin user created successfully")
            print(f"Username: {admin_user['username']}")
            print(f"Password: {admin_user['password']}")
            print(f"Role: {admin_user['role']}")
            return True
        else:
            print(f"✗ Failed to create admin user: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == "__main__":
    create_admin_user()