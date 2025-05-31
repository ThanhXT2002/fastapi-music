#!/usr/bin/env python3
"""
Firebase Authentication Test Suite
Tests the complete Firebase authentication flow
"""
import requests
import json
import jwt
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

# Firebase Token for testing (replace with fresh token when needed)
SAMPLE_FIREBASE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImZlNjVjY2I4ZWFkMGJhZWY1ZmQzNjE5NWQ2NTI4YTA1NGZiYjc2ZjMiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiVHLhuqduIFh1w6JuIFRow6BuaCIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLMVVGODQ4djZwTGRJdlo4Smk2N1duMVNCWDUyQXlHTzI5UkRuMVNsZTlXWlF1cXdsbD1zOTYtYyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS90eHQtc3lzdGVtLTkwNzg4IiwiYXVkIjoidHh0LXN5c3RlbS05MDc4OCIsImF1dGhfdGltZSI6MTc0ODY1ODg0NywidXNlcl9pZCI6IkdYeEpaOUE3eDNQczBDd2E1MU1BTXRWcDlxbjIiLCJzdWIiOiJHWHhKWjlBN3gzUHMwQ3dhNTFNQU10VnA5cW4yIiwiaWF0IjoxNzQ4NjU4ODQ3LCJleHAiOjE3NDg2NjI0NDcsImVtYWlsIjoidHJhbnh1YW50aGFuaHR4dDIwMDJAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMTE2OTU1MDA5NDg3ODAzODYzODUiXSwiZW1haWwiOlsidHJhbnh1YW50aGFuaHR4dDIwMDJAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.XMxVGoCzU4TnAWJrLF3IeyAtjEO0l3Zpb-cbmqZKsAvLlgueEnSeDHShacNboQnriVXvPgRMW2ks4tLivPLN_XgFuB5vDefAk3ZKh-GmHCElZzbXpdwLjIP6npLg9G-bytQkGn9gzkHdvQIUj_b8PwG7AAIHJrjX_RpGOaG-gkqN9vVCVqdd4BgKbjXdprnwlSBgkyWjTJZ65ZBDktkRbCx0TaTP8gy6nVM_CTx6iHzkZrN1Xezg8mt69QZRkFltr8IqC9tODjPluAhJIdf0E2jSDKdm6HGrEJHks_6Jelv_9V-uYZ5Ol_aIZgZpNfi5IKY-Lqb9gYYSI1e-gESyWQ"

def decode_token_info(token):
    """Decode token to see payload information"""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        print("=== TOKEN PAYLOAD ===")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        # Check expiration
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'])
            current_time = datetime.now()
            print(f"\nToken expires at: {exp_time}")
            print(f"Current time: {current_time}")
            print(f"Token status: {'EXPIRED' if current_time > exp_time else 'VALID'}")
            
        return payload
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def test_firebase_login():
    """Test Firebase token authentication"""
    print("=== TESTING FIREBASE LOGIN ===")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/google",
            json={"token": SAMPLE_FIREBASE_TOKEN},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ LOGIN SUCCESS!")
            print(f"User: {data['user']['name']} ({data['user']['email']})")
            return data['token']['access_token']
        else:
            print(f"❌ LOGIN FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        return None

def test_protected_endpoint(token, token_type="Firebase"):
    """Test protected endpoint with token"""
    print(f"\n=== TESTING PROTECTED ENDPOINT ({token_type}) ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/songs",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ACCESS SUCCESS! Found {len(data)} songs")
            return True
        else:
            print(f"❌ ACCESS FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ACCESS ERROR: {e}")
        return False

def test_create_song(token, token_type="Firebase"):
    """Test creating a song with token"""
    print(f"\n=== TESTING CREATE SONG ({token_type}) ===")
    
    song_data = {
        "title": f"Test Song ({token_type})",
        "artist": "Test Artist",
        "duration": 180,
        "source": "youtube"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/songs",
            json=song_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CREATE SUCCESS! Song ID: {data['id']}")
            return True
        else:
            print(f"❌ CREATE FAILED: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ CREATE ERROR: {e}")
        return False

def main():
    """Run complete test suite"""
    print("🔥 FIREBASE AUTHENTICATION TEST SUITE 🔥")
    print("=" * 50)
    
    # Check token info
    print("\n📋 Token Information:")
    payload = decode_token_info(SAMPLE_FIREBASE_TOKEN)
    
    if not payload:
        print("❌ Invalid token, aborting tests")
        return
    
    # Check if token is expired
    if 'exp' in payload:
        exp_time = datetime.fromtimestamp(payload['exp'])
        if datetime.now() > exp_time:
            print("⚠️  WARNING: Token is expired! Tests may fail.")
            print("   Please update SAMPLE_FIREBASE_TOKEN with a fresh token.")
    
    # Test Firebase login
    print("\n🔐 Authentication Tests:")
    jwt_token = test_firebase_login()
    
    # Test Firebase token direct access
    print("\n🛡️  Firebase Token Direct Access:")
    firebase_success = test_protected_endpoint(SAMPLE_FIREBASE_TOKEN, "Firebase")
    firebase_create = test_create_song(SAMPLE_FIREBASE_TOKEN, "Firebase")
    
    # Test JWT token access
    if jwt_token:
        print("\n🎫 JWT Token Access:")
        jwt_success = test_protected_endpoint(jwt_token, "JWT")
        jwt_create = test_create_song(jwt_token, "JWT")
    else:
        print("\n❌ Skipping JWT tests (no token)")
        jwt_success = jwt_create = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print(f"Firebase Login: {'✅ PASS' if jwt_token else '❌ FAIL'}")
    print(f"Firebase Direct Access: {'✅ PASS' if firebase_success else '❌ FAIL'}")
    print(f"Firebase Create: {'✅ PASS' if firebase_create else '❌ FAIL'}")
    print(f"JWT Access: {'✅ PASS' if jwt_success else '❌ FAIL'}")
    print(f"JWT Create: {'✅ PASS' if jwt_create else '❌ FAIL'}")
    
    overall_success = all([jwt_token, firebase_success, firebase_create, jwt_success, jwt_create])
    print(f"\nOverall: {'🎉 ALL TESTS PASSED!' if overall_success else '⚠️  SOME TESTS FAILED'}")

if __name__ == "__main__":
    main()
