#!/usr/bin/env python3
"""Test script to verify signup and login functionality"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_signup():
    """Test user signup"""
    print("\n" + "="*60)
    print("STEP 1: Testing Signup")
    print("="*60)
    
    user_data = {
        "email": "testuser@example.com",
        "password": "Password123!",
        "name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json=user_data,
            timeout=5
        )
        
        print(f"\nRequest: POST /api/auth/signup")
        print(f"Payload: {json.dumps(user_data, indent=2)}")
        print(f"\nStatus Code: {response.status_code}")
        
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            user_id = result.get("data", {}).get("user", {}).get("id")
            print(f"\n✅ Signup successful! User ID: {user_id}")
            return user_id, user_data
        else:
            print(f"\n❌ Signup failed!")
            return None, user_data
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None, user_data


def test_login(email, password):
    """Test user login"""
    print("\n" + "="*60)
    print("STEP 2: Testing Login")
    print("="*60)
    
    user_data = {
        "email": email,
        "password": password,
        "name": ""
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=user_data,
            timeout=5
        )
        
        print(f"\nRequest: POST /api/auth/login")
        print(f"Payload: email={email}, password={'*' * len(password)}")
        print(f"\nStatus Code: {response.status_code}")
        
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            user_info = result.get("data", {}).get("user", {})
            print(f"\n✅ Login successful!")
            print(f"   User: {user_info.get('name')} ({user_info.get('email')})")
            print(f"   Role: {user_info.get('role')}")
            return True
        else:
            print(f"\n❌ Login failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_health():
    """Test API health"""
    print("\n" + "="*60)
    print("Testing API Health")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Backend API is healthy!")
            print(f"   Status: {result.get('status')}")
            print(f"   Service: {result.get('service')}")
            return True
        else:
            print(f"❌ Backend API is not responding correctly")
            return False
            
    except Exception as e:
        print(f"❌ Cannot connect to backend: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DataChat Authentication Test Suite")
    print("="*60)
    
    # Test health
    if not test_health():
        print("\n⚠️  Backend API is not accessible. Please ensure:")
        print("   - Backend server is running on http://localhost:8000")
        print("   - Database is initialized")
        return
    
    # Test signup
    user_id, user_data = test_signup()
    
    if not user_id:
        print("\n⚠️  Signup failed. Cannot proceed with login test.")
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Test login
    test_login(user_data["email"], user_data["password"])
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Visit http://localhost:3000 to see the landing page")
    print("2. Click 'Sign Up' to create an account via the UI")
    print("3. Test the login functionality")
    print("4. Verify the dashboard loads after authentication")


if __name__ == "__main__":
    main()
