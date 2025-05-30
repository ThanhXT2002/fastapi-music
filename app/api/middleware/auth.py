from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.internal.rfc.jwt.jwt import decode_token
from app.internal.domain.errors import TokenError
from app.internal.storage.repositories.user import UserRepository
from app.internal.domain.user import User

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
        token_data = decode_token(token)
        user_repo = UserRepository(db)
        user = user_repo.find_by_email(token_data.sub)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
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
        token_data = decode_token(token)
        user_repo = UserRepository(db)
        user = user_repo.find_by_email(token_data.sub)
        return user
    except (TokenError, Exception):
        return None
