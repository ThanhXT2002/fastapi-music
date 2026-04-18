"""Route xac thuc nguoi dung (Google OAuth).

Module nay chua:
- Endpoint dang nhap bang Google ID token.

Lien quan:
- Controller: app/controllers/auth.py
- Schema:     app/schemas/auth.py
"""

# ── Standard library imports ──────────────────────────────
from typing import Annotated

# ── Third-party imports ───────────────────────────────────
from fastapi import APIRouter, Depends, status

# ── Internal imports ──────────────────────────────────────
from app.controllers.auth import AuthController, get_auth_controller
from app.schemas.auth import GoogleTokenRequest, AuthApiResponse


# ── Router / Dependencies ─────────────────────────────────

router = APIRouter(prefix="/auth", tags=["Authentication"])

AuthControllerDep = Annotated[
    AuthController, Depends(get_auth_controller)
]


# ── Endpoints ─────────────────────────────────────────────

@router.post(
    "/google",
    response_model=AuthApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with Google",
    description="Login or register a user with Google ID token",
)
def google_login(
    request: GoogleTokenRequest,
    auth_controller: AuthControllerDep,
) -> AuthApiResponse:
    """Dang nhap hoac dang ky nguoi dung bang Google ID token.

    Sau khi xac thuc thanh cong:
        - Tao hoac cap nhat thong tin nguoi dung trong database.
        - Sinh JWT access token cho cac request tiep theo.

    Args:
        request: Chua Google/Firebase ID token tu frontend.
        auth_controller: Controller xu ly nghiep vu xac thuc.

    Returns:
        JWT token va thong tin nguoi dung.

    Raises:
        HTTP 401: Token khong hop le hoac het han.
        HTTP 404: Khong tim thay nguoi dung (truong hop bat thuong).
        HTTP 500: Loi he thong khong xac dinh.
    """
    return auth_controller.google_login(request.token)