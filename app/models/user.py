"""Mo hinh du lieu nguoi dung.

Module nay chua:
- Model User luu thong tin tai khoan dang nhap qua Google OAuth.

Lien quan:
- Repository: app/internal/storage/repositories/user.py
- Controller: app/controllers/auth.py
- Schema:     app/schemas/auth.py
"""

# ── Third-party imports ───────────────────────────────────
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

# ── Internal imports ──────────────────────────────────────
from app.config.database import Base


class User(Base):
    """Bang luu tru thong tin nguoi dung da dang nhap.

    Hien tai chi ho tro dang nhap qua Google OAuth / Firebase.
    Truong google_id nullable vi co the mo rong them phuong thuc
    dang nhap khac trong tuong lai (email/password, Facebook...).

    Attributes:
        id: Primary key tu tang.
        email: Email duy nhat cua nguoi dung.
        google_id: Google account ID (nullable, unique).
        is_verified: Da xac thuc email qua Google chua.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )
