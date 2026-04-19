"""Schema xac thuc nguoi dung qua Google OAuth.

Module nay chua:
- Schema request/response cho endpoint dang nhap Google.
- AuthResponse boc trong ApiResponse chuan.

Lien quan:
- Route:      app/routes/auth.py
- Controller: app/controllers/auth.py
"""

# ── Third-party imports ───────────────────────────────────
from pydantic import BaseModel

# ── Internal imports ──────────────────────────────────────
from app.schemas.base import ApiResponse


class SyncTokenRequest(BaseModel):
    """Du lieu dau vao khi dong bo nguoi dung qua Firebase.

    Attributes:
        token: Firebase ID token nhan tu frontend sau khi
            nguoi dung xac thuc thanh cong tren app.
    """

    token: str


class TokenData(BaseModel):
    """Thong tin JWT token tra ve.

    Attributes:
        access_token: JWT token dung de xac thuc request tiep theo.
        token_type: "bearer".
    """

    access_token: str
    token_type: str


class UserData(BaseModel):
    """Thong tin nguoi dung tra ve.

    Attributes:
        id: Firebase UID.
        email: Email tai khoan.
        name: Ten hien thi.
        profile_picture: URL anh dai dien.
        signup_provider: Phuong thuc dang ky ban dau.
        is_verified: Trang thai xac thuc email.
    """

    id: str
    email: str
    name: str | None = None
    profile_picture: str | None = None
    signup_provider: str | None = None
    is_verified: bool | None = None


class AuthData(BaseModel):
    """Payload data tra ve khi dang nhap thanh cong.

    Attributes:
        token: JWT token thong tin.
        user: Thong tin nguoi dung da dang nhap.
    """

    token: TokenData
    user: UserData


# Re-export de backwards compatible voi code cu import AuthResponse
AuthResponse = ApiResponse[AuthData]

# Alias de route co the dung response_model
AuthApiResponse = ApiResponse[AuthData]
