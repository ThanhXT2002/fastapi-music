"""Dich vu tich hop voi Firebase Authentication.

Module nay chua:
- Khoi tao firebase_admin dua tren Service Account tu bien moi truong.
- Ham verify_firebase_token de giai ma va chung thuc do an toan cua token.

Lien quan:
- Router: app/routes/auth_routes.py
- Doc: notes/AUTH_IMPLEMENTATION_GUIDE.md
"""

import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from app.config.config import settings
import logging

logger = logging.getLogger(__name__)

# Chi khoi tao bieu tuong app mot lan duy nhat
try:
    if not firebase_admin._apps:
        # Load from environment variable / settings
        service_account_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY
        
        # Check fallback
        if not service_account_path or not os.path.exists(service_account_path):
            logger.warning(
                f"[FIREBASE] WARNING: Service account file '{service_account_path}' not found! "
                "Firebase Auth will fail unless configured."
            )
        else:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("[FIREBASE] Initialized Firebase Admin successfully.")
except Exception as e:
    logger.error(f"[FIREBASE] Failed to initialize Firebase Admin: {e}")


def verify_firebase_token(id_token: str) -> dict:
    """Xac thuc id_token voi Firebase server va trich xuat user data.
    
    Args:
        id_token: Chuoi token tu client Expo.
        
    Returns:
        Dict chua cac thong tin: uid, email, name, picture, email_verified, ...
        
    Raises:
        HTTPException(401) neu token sai hoac het han.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
            "email_verified": decoded_token.get("email_verified", False),
            "firebase": decoded_token.get("firebase", {})
        }
    except Exception as e:
        logger.error(f"[FIREBASE] Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token."
        )
