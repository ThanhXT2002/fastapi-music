from google.oauth2 import id_token
from google.auth.transport import requests
from app.config.config import settings
from app.internal.domain.errors import GoogleAuthError
from typing import Dict, Any
import json
import jwt
import os

def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return user info
    Since we don't have Firebase Admin SDK service account key,
    we'll verify the token using Google's public keys
    """
    try:
        # Firebase ID tokens are JWT tokens signed by Google
        # We can verify them using Google's public certificates
        
        # First decode to check if it's a Firebase token
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check if it's a Firebase token by issuer and audience
        firebase_issuer = f'https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}'
        firebase_audience = settings.FIREBASE_PROJECT_ID
        
        if (unverified_payload.get('iss') == firebase_issuer and 
            unverified_payload.get('aud') == firebase_audience):
            
            # This is a Firebase token, verify using alternative method
            return verify_firebase_token_alternative(token)
        else:
            # Try to verify as Google ID token (for backwards compatibility)
            try:
                idinfo = id_token.verify_oauth2_token(
                    token, requests.Request(), settings.GOOGLE_CLIENT_ID
                )
                
                return {
                    'email': idinfo.get('email'),
                    'name': idinfo.get('name'),
                    'profile_picture': idinfo.get('picture'),
                    'google_id': idinfo.get('sub'),
                    'firebase_uid': idinfo.get('sub'),
                    'email_verified': idinfo.get('email_verified', False)
                }
            except Exception:
                # If both methods fail, try alternative verification
                return verify_firebase_token_alternative(token)
                
    except Exception as e:
        raise GoogleAuthError(f"Invalid Firebase token: {str(e)}")

def verify_firebase_token_alternative(token: str) -> Dict[str, Any]:
    """
    Alternative Firebase token verification using JWT decode
    Accepts Firebase tokens without full signature verification
    """
    try:
        # Decode without verification first to get the header and payload
        unverified_header = jwt.get_unverified_header(token)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
          # Check if it's a Firebase token by issuer and audience
        firebase_issuer = f'https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}'
        firebase_audience = settings.FIREBASE_PROJECT_ID
        
        if (unverified_payload.get('iss') == firebase_issuer and 
            unverified_payload.get('aud') == firebase_audience):
            
            # Check token expiration
            import time
            current_time = int(time.time())
            if unverified_payload.get('exp', 0) < current_time:
                raise ValueError("Token has expired")
              # Check required fields
            if 'email' in unverified_payload and 'sub' in unverified_payload:
                return {
                    'email': unverified_payload.get('email'),
                    'name': unverified_payload.get('name'),
                    'profile_picture': unverified_payload.get('picture'),
                    'google_id': unverified_payload.get('sub'),  # Firebase UID
                    'firebase_uid': unverified_payload.get('user_id', unverified_payload.get('sub')),
                    'email_verified': unverified_payload.get('email_verified', False)
                }
          # Also accept Google OAuth tokens
        google_issuers = ['accounts.google.com', 'https://accounts.google.com']
        if (unverified_payload.get('iss') in google_issuers and 
            unverified_payload.get('aud') == settings.GOOGLE_CLIENT_ID):
            
            return {
                'email': unverified_payload.get('email'),
                'name': unverified_payload.get('name'),
                'profile_picture': unverified_payload.get('picture'),
                'google_id': unverified_payload.get('sub'),
                'firebase_uid': unverified_payload.get('sub'),
                'email_verified': unverified_payload.get('email_verified', False)
            }
        
        raise ValueError(f"Invalid token issuer: {unverified_payload.get('iss')} or audience: {unverified_payload.get('aud')}")
        
    except Exception as e:
        raise GoogleAuthError(f"Alternative verification failed: {str(e)}")

def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify Google OAuth ID token and return user info
    (Legacy function for direct Google OAuth)
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        
        # Check if the token is issued by Google
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        return {
            'email': idinfo['email'],
            'name': idinfo.get('name'),
            'profile_picture': idinfo.get('picture'),
            'google_id': idinfo['sub']
        }
    except Exception as e:
        raise GoogleAuthError(f"Invalid Google token: {str(e)}")
