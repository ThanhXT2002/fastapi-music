from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.internal.rfc.jwt.jwt import decode_token
from app.internal.model.errors import TokenError, GoogleAuthError
from app.internal.storage.repositories.user import UserRepository
from app.internal.model.user import User
from app.internal.utils.helpers import verify_firebase_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Try to decode as JWT token first (from /auth/google login)
        try:
            token_data = decode_token(token)
            user_repo = UserRepository(db)
            user = user_repo.find_by_email(token_data.sub)
            
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            return user
            
        except TokenError:
            # If JWT decode fails, try Firebase ID token verification
            try:
                user_info = verify_firebase_token(token)
                user_repo = UserRepository(db)
                
                # Find user by google_id (Firebase UID)
                user = user_repo.find_by_google_id(user_info['google_id'])
                
                if user is None:
                    # Try to find by email
                    user = user_repo.find_by_email(user_info['email'])
                    
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                    
                return user
                
            except GoogleAuthError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user_optional(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None"""
    if not token:
        return None
    
    try:
        # Try JWT token first
        try:
            token_data = decode_token(token)
            user_repo = UserRepository(db)
            user = user_repo.find_by_email(token_data.sub)
            return user
        except TokenError:
            # Try Firebase token
            try:
                user_info = verify_firebase_token(token)
                user_repo = UserRepository(db)
                
                # Find user by google_id or email
                user = user_repo.find_by_google_id(user_info['google_id'])
                if not user:
                    user = user_repo.find_by_email(user_info['email'])
                
                return user
            except (GoogleAuthError, Exception):
                return None
    except Exception:
        return None
