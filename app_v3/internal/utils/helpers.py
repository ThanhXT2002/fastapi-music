from google.oauth2 import id_token
from google.auth.transport import requests
from app_v3.config.config import settings
from app_v3.internal.model.errors import GoogleAuthError
from typing import Dict, Any
import jwt

def verify_firebase_token(token: str) -> Dict[str, Any]:
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        firebase_issuer = f'https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}'
        firebase_audience = settings.FIREBASE_PROJECT_ID
        if (unverified_payload.get('iss') == firebase_issuer and 
            unverified_payload.get('aud') == firebase_audience):
            return verify_firebase_token_alternative(token)
        else:
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
                return verify_firebase_token_alternative(token)
    except Exception as e:
        raise GoogleAuthError(f"Invalid Firebase token: {str(e)}")

def verify_firebase_token_alternative(token: str) -> Dict[str, Any]:
    try:
        unverified_header = jwt.get_unverified_header(token)
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        firebase_issuer = f'https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}'
        firebase_audience = settings.FIREBASE_PROJECT_ID
        if (unverified_payload.get('iss') == firebase_issuer and 
            unverified_payload.get('aud') == firebase_audience):
            import time
            current_time = int(time.time())
            if unverified_payload.get('exp', 0) < current_time:
                raise ValueError("Token has expired")
            if 'email' in unverified_payload and 'sub' in unverified_payload:
                return {
                    'email': unverified_payload.get('email'),
                    'name': unverified_payload.get('name'),
                    'profile_picture': unverified_payload.get('picture'),
                    'google_id': unverified_payload.get('sub'),
                    'firebase_uid': unverified_payload.get('user_id', unverified_payload.get('sub')),
                    'email_verified': unverified_payload.get('email_verified', False)
                }
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
        raise ValueError(f"Invalid token issuer: {unverified_payload.get('iss')} or audience:   {unverified_payload.get('aud')}")
    except Exception as e:
        raise GoogleAuthError(f"Alternative verification failed: {str(e)}")
