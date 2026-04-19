"""Xu ly nghiep vu xac thuc nguoi dung qua Google OAuth.

Module nay chua:
- AuthController: xac thuc Firebase token, tao/cap nhat user, sinh JWT.
- get_auth_controller: function dependency de inject vao route.

Lien quan:
- Route:      app/routes/auth.py
- Repository: app/internal/storage/repositories/user.py
- JWT:        app/internal/rfc/jwt/jwt.py
- Helpers:    app/internal/utils/helpers.py
"""

# ── Standard library imports ──────────────────────────────
from datetime import timedelta
from typing import Annotated

# ── Third-party imports ───────────────────────────────────
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# ── Internal imports ──────────────────────────────────────
from app.config.database import get_db
from app.config.config import settings
from app.services.firebase_service import verify_firebase_token
from app.models.errors import UserNotFoundError
from app.internal.storage.repositories.user import UserRepository
from app.internal.rfc.jwt.jwt import create_access_token
from app.schemas.base import ApiResponse
from app.schemas.auth import AuthData, TokenData, UserData


class AuthController:
    """Xu ly xac thuc va quan ly phien dang nhap nguoi dung.

    Chiu trach nhiem:
        - Xac thuc Firebase ID token.
        - Tao nguoi dung moi hoac cap nhat thong tin.
        - Sinh JWT access token cho app.
    """

    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def sync_user(self, firebase_token: str) -> ApiResponse[AuthData]:
        """Xac thuc Firebase token va tra ve JWT cung thong tin user.

        Flow xu ly:
            1. Verify Firebase ID token.
            2. Tim user theo uid.
            3. Neu chua co: tao user moi (kem theo p/t dang ky bg metadata).
            4. Sinh JWT access token.

        Args:
            firebase_token: Firebase ID token tu frontend.

        Returns:
            AuthResponse gom app token va thong tin nguoi dung.
            
        Raises:
            HTTPException
        """
        try:
            # 1. Giai ma token tu Firebase
            user_info = verify_firebase_token(firebase_token)
            uid = user_info['uid']

            # 2. Tim user theo UID
            user = self.user_repo.find_by_uid(uid)

            if not user:
                # 3. Neu chua co -> Tao user moi
                provider = user_info.get("firebase", {}).get("sign_in_provider", "email")
                user = self.user_repo.create({
                    'id': uid,
                    'email': user_info['email'],
                    'name': user_info.get('name'),
                    'profile_picture': user_info.get('picture'),
                    'is_verified': user_info.get('email_verified', False),
                    'signup_provider': provider
                })
            else:
                # Cap nhat vao DB neu user co thay doi gi do tren Firebase
                user = self.user_repo.update(uid, {
                    'is_verified': user_info.get('email_verified', user.is_verified),
                    'name': user_info.get('name', user.name),
                    'profile_picture': user_info.get('picture', user.profile_picture),
                })

            # 4. Sinh JWT token cua Backend
            token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            token = create_access_token(
                data={"sub": user.id},  # UUID/string UID
                expires_delta=token_expires,
            )

            auth_data = AuthData(
                token=TokenData(
                    access_token=token,
                    token_type="bearer",
                ),
                user=UserData(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    profile_picture=user.profile_picture,
                    signup_provider=user.signup_provider,
                    is_verified=user.is_verified,
                ),
            )
            return ApiResponse.ok(data=auth_data, message="Đăng nhập thành công")

        except Exception as e:
            # Neu da la HTTPException do verify_firebase_token ban ra thi throw luon
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )


# ── Dependencies ──────────────────────────────────────────

def get_auth_controller(
    db: Annotated[Session, Depends(get_db)],
) -> AuthController:
    """Tao instance AuthController voi db session da inject.

    Dung lam dependency trong router cua auth domain.
    Session db se tu dong dong sau khi request ket thuc.
    """
    return AuthController(db)
