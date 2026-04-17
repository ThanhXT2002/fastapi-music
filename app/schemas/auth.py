"""Schema xac thuc nguoi dung qua Google OAuth.

Module nay chua:
- Schema request/response cho endpoint dang nhap Google.

Lien quan:
- Route:      app/routes/auth.py
- Controller: app/controllers/auth.py
"""

# ── Third-party imports ───────────────────────────────────
from pydantic import BaseModel


class GoogleTokenRequest(BaseModel):
    """Du lieu dau vao khi dang nhap bang Google.

    Attributes:
        token: Firebase ID token nhan tu frontend sau khi
            nguoi dung dang nhap Google tren client.
    """

    token: str


class TokenResponse(BaseModel):
    """Thong tin JWT token tra ve cho frontend.

    Attributes:
        access_token: JWT token dung de xac thuc cac request tiep theo.
        token_type: Loai token, luon la "bearer".
    """

    access_token: str
    token_type: str


class UserResponse(BaseModel):
    """Thong tin nguoi dung tra ve sau khi dang nhap thanh cong.

    Attributes:
        id: ID nguoi dung trong database.
        email: Email tai khoan Google.
        name: Ten hien thi (nullable neu Google khong cung cap).
        profile_picture: URL anh dai dien tu Google.
        is_verified: Trang thai xac thuc email.
    """

    id: int
    email: str
    name: str | None = None
    profile_picture: str | None = None
    is_verified: bool | None = None


class AuthResponse(BaseModel):
    """Response tong hop gom token va thong tin nguoi dung.

    Attributes:
        token: JWT token thong tin.
        user: Thong tin nguoi dung da dang nhap.
    """

    token: TokenResponse
    user: UserResponse
