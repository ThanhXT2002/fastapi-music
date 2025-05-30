from google.oauth2 import id_token
from google.auth.transport import requests
from app.config.config import settings
from app.internal.domain.errors import GoogleAuthError
from typing import Dict, Any

def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify Google ID token and return user info
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
