#!/usr/bin/env python3
"""
Simple API test script to verify the backend is working
Run this after starting the server with: python start.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_docs_endpoint():
    """Test the docs endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"✅ Docs endpoint: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Docs endpoint failed: {e}")
        return False

def main():
    print("🧪 Testing Asset Validation API...")
    print("=" * 50)
    
    tests = [
        test_root_endpoint,
        test_health_endpoint,
        test_docs_endpoint
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All basic tests passed! Your API is ready for hosting.")
    else:
        print("⚠️  Some tests failed. Check the server is running on http://localhost:8000")

if __name__ == "__main__":
    main()