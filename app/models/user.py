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
    """Bang luu tru thong tin nguoi dung da dang nhap."""

    __tablename__ = "users"

    id = Column(String(50), primary_key=True) # Sử dụng Firebase UID làm Primary Key
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    signup_provider = Column(String(50), default="email") # Lưu vết phương thức ĐĂNG KÝ lần đầu tiên
    is_verified = Column(Boolean, default=False) # Lấy từ Firebase email_verified
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )
