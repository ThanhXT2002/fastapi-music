from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import jwt, JWTError
from pydantic import BaseModel
from app.config.config import settings
from app.internal.model.errors import TokenError

class TokenPayload(BaseModel):
    sub: str
    exp: int

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        claims=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate JWT token
    """
    try:
        payload = jwt.decode(
            token=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        token_data = TokenPayload(
            sub=payload["sub"],
            exp=payload["exp"]
        )
        
        if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            raise TokenError("Token expired")
            
        return token_data
    except JWTError:
        raise TokenError("Invalid token")
