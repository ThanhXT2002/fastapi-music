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
from app.internal.utils.helpers import verify_firebase_token
from app.models.errors import GoogleAuthError, UserNotFoundError
from app.internal.storage.repositories.user import UserRepository
from app.internal.rfc.jwt.jwt import create_access_token
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse


class AuthController:
    """Xu ly xac thuc va quan ly phien dang nhap nguoi dung.

    Chiu trach nhiem:
        - Xac thuc Firebase/Google ID token.
        - Tao nguoi dung moi hoac cap nhat thong tin Google.
        - Sinh JWT access token cho frontend.

    Khong nen dung truc tiep — inject qua get_auth_controller.
    """

    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def google_login(self, token: str) -> AuthResponse:
        """Xac thuc Google token va tra ve JWT cung thong tin user.

        Flow xu ly:
            1. Verify Firebase ID token.
            2. Tim user theo google_id.
            3. Neu chua co: tim theo email (truong hop dang ky
               cung email nhung khac phuong thuc).
            4. Neu van chua co: tao user moi.
            5. Sinh JWT access token.

        Args:
            token: Firebase ID token tu frontend.

        Returns:
            AuthResponse gom JWT token va thong tin nguoi dung.

        Raises:
            HTTPException 401: Token khong hop le.
            HTTPException 404: Khong tim thay nguoi dung.
            HTTPException 500: Loi he thong khong xac dinh.
        """
        try:
            user_info = verify_firebase_token(token)

            user = self.user_repo.find_by_google_id(
                user_info['google_id']
            )

            if not user:
                # Tim theo email — truong hop user da ton tai
                # nhung dang nhap bang phuong thuc khac truoc do
                user = self.user_repo.find_by_email(
                    user_info['email']
                )

                if user:
                    user = self.user_repo.update(user.id, {
                        'google_id': user_info['google_id'],
                        'is_verified': True,
                        'name': user_info.get('name', user.name),
                        'profile_picture': user_info.get(
                            'profile_picture', user.profile_picture
                        ),
                    })
                else:
                    user = self.user_repo.create({
                        'email': user_info['email'],
                        'name': user_info.get('name'),
                        'profile_picture': user_info.get(
                            'profile_picture'
                        ),
                        'google_id': user_info['google_id'],
                        'is_verified': True,
                    })

            token_expires = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            token = create_access_token(
                data={"sub": user.email},
                expires_delta=token_expires,
            )

            return AuthResponse(
                token=TokenResponse(
                    access_token=token,
                    token_type="bearer",
                ),
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    profile_picture=user.profile_picture,
                    is_verified=user.is_verified,
                ),
            )

        except GoogleAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except Exception as e:
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
