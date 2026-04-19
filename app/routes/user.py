"""Route thong tin nguoi dung dang nhap.

Module nay chua:
- Endpoint GET /users/me tra ve profile nguoi dung hien tai.

Lien quan:
- JWT:        app/internal/rfc/jwt/jwt.py
- Repository: app/internal/storage/repositories/user.py
- Schema:     app/schemas/auth.py
"""

# ── Standard library imports ──────────────────────────────
from typing import Annotated

# ── Third-party imports ───────────────────────────────────
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# ── Internal imports ──────────────────────────────────────
from app.config.database import get_db
from app.internal.rfc.jwt.jwt import decode_token
from app.internal.storage.repositories.user import UserRepository
from app.schemas.auth import UserData
from app.schemas.base import ApiResponse


# ── Router / Dependencies ─────────────────────────────────

router = APIRouter(prefix="/users", tags=["Users"])

security = HTTPBearer()


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """Giai ma JWT va tra ve user ID (sub) tu token.

    Raises:
        HTTPException(401): Neu token khong hop le.
    """
    try:
        payload = decode_token(credentials.credentials)
        return payload.sub
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token khong hop le hoac het han.",
        )


# ── Endpoints ─────────────────────────────────────────────

@router.get(
    "/me",
    response_model=ApiResponse[UserData],
    summary="Lay thong tin nguoi dung hien tai",
)
def get_me(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[UserData]:
    """Tra ve profile cua nguoi dung dang dang nhap.

    Doc user_id tu JWT token trong Authorization header,
    sau do truy van database de tra ve thong tin day du.

    Returns:
        Thong tin user: id, email, name, profile_picture, ...

    Raises:
        HTTP 401: Token khong hop le.
        HTTP 404: Khong tim thay user trong database.
    """
    repo = UserRepository(db)
    user = repo.find_by_uid(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay nguoi dung.",
        )

    return ApiResponse.ok(
        data=UserData(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_picture=user.profile_picture,
            signup_provider=user.signup_provider,
            is_verified=user.is_verified,
        ),
        message="Lay thong tin nguoi dung thanh cong",
    )
