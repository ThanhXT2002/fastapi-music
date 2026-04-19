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
from app.schemas.auth import SyncTokenRequest, AuthApiResponse


# ── Router / Dependencies ─────────────────────────────────

router = APIRouter(prefix="/auth", tags=["Authentication"])

AuthControllerDep = Annotated[
    AuthController, Depends(get_auth_controller)
]


# ── Endpoints ─────────────────────────────────────────────

@router.post(
    "/sync",
    response_model=AuthApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync User with Firebase",
    description="Sync a Firebase user session with Backend to generate local access token.",
)
def sync_user(
    request: SyncTokenRequest,
    auth_controller: AuthControllerDep,
) -> AuthApiResponse:
    """Đồng bộ ứng dụng với Firebase Token.

    Sau khi xac thuc thanh cong tren client bang Firebase SDK,
    gui ID Token ve day de Backend kiem tra va tao local session JWT.

    Args:
        request: Chua Firebase ID token tu frontend.
        auth_controller: Controller xu ly nghiep vu xac thuc.

    Returns:
        JWT token va thong tin nguoi dung.

    Raises:
        HTTP 401: Token khong hop le hoac het han.
        HTTP 500: Loi he thong khong xac dinh.
    """
    return auth_controller.sync_user(request.token)