#!/usr/bin/env python3
"""
Test script for admin API endpoints
"""
import requests
import json
import csv
import io
import os

BASE_URL = "http://localhost:8000"

def test_admin_endpoints():
    """Test all admin endpoints"""
    
    # First, create an admin user (you'll need to do this manually in your database)
    print("=== Testing Admin API Endpoints ===\n")
    
    # Login as admin (replace with actual admin credentials)
    admin_login = {
        "username": os.getenv("ADMIN_USERNAME", "[admin_username]"),
        "password": os.getenv("ADMIN_PASSWORD", "[admin_password]")
    }
    
    print("1. Logging in as admin...")
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✓ Admin login successful")
        else:
            print(f"✗ Admin login failed: {response.text}")
            return
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return
    
    # Test asset creation
    print("\n2. Testing asset creation...")
    test_asset = {
        "tag": "TEST001",
        "name": "Test Laptop",
        "category": "IT Equipment",
        "assigned_to": "john.doe",
        "location": "Office A",
        "purchase_cost": 1200.00,
        "status": "Active"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/admin/assets", json=test_asset, headers=headers)
        if response.status_code == 200:
            asset_id = response.json()["asset"]["id"]
            print(f"✓ Asset created successfully (ID: {asset_id})")
        else:
            print(f"✗ Asset creation failed: {response.text}")
            return
    except Exception as e:
        print(f"✗ Error creating asset: {e}")
        return
    
    # Test asset update
    print("\n3. Testing asset update...")
    update_data = {
        "name": "Updated Test Laptop",
        "location": "Office B"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/admin/assets/{asset_id}", json=update_data, headers=headers)
        if response.status_code == 200:
            print("✓ Asset updated successfully")
        else:
            print(f"✗ Asset update failed: {response.text}")
    except Exception as e:
        print(f"✗ Error updating asset: {e}")
    
    # Test user creation
    print("\n4. Testing user creation...")
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "auditor"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/admin/users", json=test_user, headers=headers)
        if response.status_code == 200:
            user_id = response.json()["user"]["id"]
            print(f"✓ User created successfully (ID: {user_id})")
        else:
            print(f"✗ User creation failed: {response.text}")
            user_id = None
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        user_id = None
    
    # Test user list
    print("\n5. Testing user list...")
    try:
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()["users"]
            print(f"✓ Retrieved {len(users)} users")
        else:
            print(f"✗ User list failed: {response.text}")
    except Exception as e:
        print(f"✗ Error listing users: {e}")
    
    # Test bulk import (create sample CSV)
    print("\n6. Testing bulk import...")
    csv_data = """tag,name,category,assigned_to,location,purchase_cost,status
BULK001,Bulk Laptop 1,IT Equipment,user1,Office A,1000.00,Active
BULK002,Bulk Laptop 2,IT Equipment,user2,Office B,1100.00,Active
BULK003,Bulk Monitor,IT Equipment,user3,Office C,300.00,Active"""
    
    try:
        files = {'file': ('test_assets.csv', csv_data, 'text/csv')}
        response = requests.post(f"{BASE_URL}/admin/assets/bulk-import", files=files, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Bulk import completed: {result['success_count']} success, {result['error_count']} errors")
        else:
            print(f"✗ Bulk import failed: {response.text}")
    except Exception as e:
        print(f"✗ Error with bulk import: {e}")
    
    # Cleanup - delete test asset
    print("\n7. Cleaning up test asset...")
    try:
        response = requests.delete(f"{BASE_URL}/admin/assets/{asset_id}", headers=headers)
        if response.status_code == 200:
            print("✓ Test asset deleted")
        else:
            print(f"✗ Asset deletion failed: {response.text}")
    except Exception as e:
        print(f"✗ Error deleting asset: {e}")
    
    # Cleanup - delete test user
    if user_id:
        print("\n8. Cleaning up test user...")
        try:
            response = requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=headers)
            if response.status_code == 200:
                print("✓ Test user deleted")
            else:
                print(f"✗ User deletion failed: {response.text}")
        except Exception as e:
            print(f"✗ Error deleting user: {e}")
    
    print("\n=== Admin API Testing Complete ===")

if __name__ == "__main__":
    test_admin_endpoints()