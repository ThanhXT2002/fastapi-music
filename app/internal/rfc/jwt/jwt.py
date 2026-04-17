"""Utilities xu ly JSON Web Token (JWT) cho authentication.

Module nay cung cap cac ham tao va verify token su dung thu vien python-jose.
Dua vao config tu app.config.config.settings.

Lien quan:
- Models: app/models/errors.py
- Config: app/config/config.py
"""

# ── Standard library imports ──────────────────────────────
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# ── Third-party imports ───────────────────────────────────
from jose import jwt, JWTError
from pydantic import BaseModel

# ── Internal imports ──────────────────────────────────────
from app.config.config import settings
from app.models.errors import TokenError


class TokenPayload(BaseModel):
    """Schema du lieu payload tra ve sau khi giai ma JWT.

    Attributes:
        sub (str): Subject (email cua user).
        exp (int): Thoi gian het han token (timestamp).
    """
    sub: str
    exp: int


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Sinh JWT access token moi.

    Su dung thuat toan va secret key cau hinh trong settings.
    Thoi gian het han mac dinh la ACCESS_TOKEN_EXPIRE_MINUTES neu khong truyen.

    Args:
        data: Dict chua du lieu thong tin payload (thuong la {"sub": email}).
        expires_delta: Thoi gian song cua token (tuy chon).

    Returns:
        Chuoi JWT token dang string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        claims=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> TokenPayload:
    """Giai ma va xac thuc kiem tra JWT token.

    Args:
        token: Chuoi string JWT.

    Returns:
        Doi tuong TokenPayload chua sub va exp.

    Raises:
        TokenError: Neu token het han hoac khong the giai ma.
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
