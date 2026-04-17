"""Cau hinh ung dung doc tu bien moi truong (.env).

Module nay chua:
- Class Settings voi tat ca cau hinh: database, JWT, Google OAuth,
  Firebase, Cloudinary, thu muc upload.
- Instance ``settings`` dung toan cuc trong ung dung.

Lien quan:
- Database: database.py (doc DATABASE_URL tu day)
- Auth:     app/internal/utils/helpers.py (doc FIREBASE_PROJECT_ID)
"""

# ── Third-party imports ───────────────────────────────────
from pydantic_settings import BaseSettings

# ── Standard library imports ──────────────────────────────
import os

from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Cau hinh toan cuc cua ung dung, doc tu bien moi truong.

    Attributes:
        PROJECT_NAME: Ten hien thi cua API tren Swagger docs.
        DATABASE_URL: Connection string toi database (SQLite/PostgreSQL).
        SECRET_KEY: Khoa bi mat dung de ky JWT token.
        ALGORITHM: Thuat toan ma hoa JWT (mac dinh HS256).
        ACCESS_TOKEN_EXPIRE_MINUTES: Thoi gian het han token (phut).
        FIREBASE_PROJECT_ID: Project ID tren Firebase dung xac thuc.
        AUDIO_DIRECTORY: Thu muc luu file audio da download.
        THUMBNAIL_DIRECTORY: Thu muc luu file thumbnail da download.
        ALLOW_ORIGINS: Danh sach origin duoc phep CORS.
    """

    PROJECT_NAME: str = "FastAPI Music API"
    API_PREFIX: str = "/api/v1"
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    FIREBASE_PROJECT_ID: str = os.getenv(
        "FIREBASE_PROJECT_ID", os.getenv("GOOGLE_PROJECT_ID", "")
    )
    FIREBASE_SERVICE_ACCOUNT_KEY: str = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_KEY", "./document/key-auth-google.json"
    )
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIRECTORY", "./uploads")
    AUDIO_DIRECTORY: str = os.getenv("AUDIO_DIRECTORY", "./uploads/audio")
    THUMBNAIL_DIRECTORY: str = os.getenv(
        "THUMBNAIL_DIRECTORY", "./uploads/thumbnails"
    )
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "musicadmin")
    ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    ADMIN_SECRET_KEY: str = os.getenv(
        "ADMIN_SECRET_KEY",
        "your-very-secure-admin-secret-key-change-this",
    )
    ALLOW_ORIGINS: list[str] = []


settings = Settings()
