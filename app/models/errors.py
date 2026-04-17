"""Dinh nghia cac exception tuy chinh cho ung dung.

Module nay chua:
- Exception cho xac thuc (AuthError, GoogleAuthError, TokenError).
- Exception cho nghiep vu (UserNotFoundError, SongNotFoundError).

Lien quan:
- Auth:       app/controllers/auth.py (raise GoogleAuthError)
- JWT:        app/internal/rfc/jwt/jwt.py (raise TokenError)
- Controller: app/controllers/song_controller.py (raise SongNotFoundError)
"""


class AuthError(Exception):
    """Loi xac thuc chung, lop cha cua cac loi auth cu the."""

    def __init__(self, message: str = "Authentication error"):
        self.message = message
        super().__init__(self.message)


class GoogleAuthError(AuthError):
    """Xac thuc Google OAuth / Firebase that bai."""


class TokenError(AuthError):
    """JWT token khong hop le hoac da het han."""


class UserNotFoundError(Exception):
    """Khong tim thay nguoi dung trong database."""

    def __init__(self, message: str = "User not found"):
        self.message = message
        super().__init__(self.message)


class SongNotFoundError(Exception):
    """Khong tim thay bai hat trong database."""

    def __init__(self, message: str = "Song not found"):
        self.message = message
        super().__init__(self.message)
