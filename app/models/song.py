"""Mo hinh du lieu bai hat va trang thai xu ly.

Module nay chua:
- Enum ProcessingStatus dinh nghia cac trang thai pipeline download.
- Model Song luu thong tin bai hat, trang thai xu ly, duong dan file.

Lien quan:
- Service:    app/services/youtube_service.py (cap nhat trang thai)
- Controller: app/controllers/song_controller.py (truy van)
- Schema:     app/schemas/song.py (serialization)
"""

# ── Standard library imports ──────────────────────────────
import enum
from datetime import datetime

# ── Third-party imports ───────────────────────────────────
from sqlalchemy import (
    Column, String, Integer, DateTime, Text,
    Enum as SQLEnum, Index,
)

# ── Internal imports ──────────────────────────────────────
from app.config.database import Base


class ProcessingStatus(enum.Enum):
    """Cac trang thai xu ly cua pipeline download bai hat.

    Thu tu chuyen trang thai hop le:
        PENDING -> PROCESSING -> COMPLETED
        PENDING -> PROCESSING -> FAILED
    """

    PENDING = "pending"
    """Bai hat moi tao, chua bat dau download."""

    PROCESSING = "processing"
    """Dang download audio va thumbnail tu YouTube."""

    COMPLETED = "completed"
    """Download va convert thanh cong, file san sang phuc vu."""

    FAILED = "failed"
    """Download hoac convert that bai, xem error_message."""


class Song(Base):
    """Bang luu tru thong tin bai hat va trang thai download.

    Quan he:
        - Mot Song co the thuoc nhieu User qua bang user_songs.

    Attributes:
        id: YouTube video ID, dung lam primary key.
        title: Tieu de bai hat lay tu YouTube metadata.
        artist: Ten kenh/nghe si upload video.
        status: Trang thai xu ly hien tai cua bai hat.
        audio_filename: Ten file audio da download (null khi chua xong).
        thumbnail_filename: Ten file thumbnail (null khi chua xong).
    """

    __tablename__ = "songs"

    id = Column(String(50), primary_key=True)
    title = Column(String(500), nullable=False)
    artist = Column(String(300), nullable=True)
    thumbnail_url = Column(Text, nullable=False)
    duration = Column(Integer, nullable=False)
    duration_formatted = Column(String(20), nullable=False)
    keywords = Column(Text, nullable=True)
    original_url = Column(Text, nullable=False)

    # Index vi thuong xuyen filter theo status o trang danh sach
    status = Column(
        SQLEnum(ProcessingStatus),
        default=ProcessingStatus.PENDING,
        nullable=False,
    )

    # Nullable — chua co file khi dang download
    audio_filename = Column(String(300), nullable=True)
    thumbnail_filename = Column(String(300), nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_songs_status', 'status'),
        Index('idx_songs_created_at', 'created_at'),
        Index(
            'idx_songs_status_completed_at', 'status', 'completed_at'
        ),
    )
