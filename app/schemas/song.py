"""Schema du lieu bai hat va response API.

Module nay chua:
- Enum ProcessingStatus (ban Pydantic, song song voi models/song.py).
- Schema request/response cho cac endpoint bai hat.
- Schema APIResponse chung cho toan bo API.

Lien quan:
- Route:      app/routes/song_routes.py
- Controller: app/controllers/song_controller.py
- Model:      app/models/song.py
"""

# ── Standard library imports ──────────────────────────────
from datetime import datetime
from enum import Enum

# ── Third-party imports ───────────────────────────────────
from pydantic import BaseModel, Field, field_validator

# ── Internal imports ──────────────────────────────────────
from app.schemas.base import ApiResponse as APIResponse  # noqa: F401 — re-export


class ProcessingStatus(str, Enum):
    """Trang thai xu ly bai hat (ban Pydantic cho serialization)."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SongInfoRequest(BaseModel):
    """Du lieu dau vao khi yeu cau lay thong tin bai hat.

    Attributes:
        youtube_url: URL YouTube hop le cua bai hat can xu ly.
    """

    youtube_url: str


class SongInfoResponse(BaseModel):
    """Thong tin metadata bai hat tra ve sau khi truy xuat tu YouTube.

    Attributes:
        id: YouTube video ID.
        title: Tieu de bai hat.
        artist: Ten nghe si / kenh upload.
        thumbnail_url: URL anh thumbnail tu YouTube.
        duration: Thoi luong tinh bang giay.
        duration_formatted: Thoi luong da format (MM:SS).
        keywords: Danh sach tags tu YouTube metadata.
        original_url: URL goc cua video.
        created_at: Thoi diem tao ban ghi trong database.
    """

    id: str
    title: str
    artist: str | None
    thumbnail_url: str
    duration: int
    duration_formatted: str
    keywords: list[str]
    original_url: str
    created_at: datetime


class StatusResponse(BaseModel):
    """Trang thai xu ly hien tai cua mot bai hat.

    Attributes:
        id: YouTube video ID.
        status: Trang thai xu ly (pending/processing/completed/failed).
        progress: Tien do xu ly tu 0.0 den 1.0 (nullable).
        error_message: Thong bao loi neu status = failed.
        audio_filename: Ten file audio da download.
        thumbnail_filename: Ten file thumbnail da download.
        updated_at: Thoi diem cap nhat trang thai gan nhat.
    """

    id: str
    status: ProcessingStatus
    progress: float | None = None
    error_message: str | None = None
    audio_filename: str | None = None
    thumbnail_filename: str | None = None
    updated_at: datetime




class CompletedSongResponse(BaseModel):
    """Thong tin bai hat da hoan thanh kem URL streaming.

    Attributes:
        id: YouTube video ID.
        title: Tieu de bai hat.
        artist: Ten nghe si.
        duration: Thoi luong (giay).
        duration_formatted: Thoi luong da format (MM:SS).
        thumbnail_url: URL endpoint thumbnail tren server.
        audio_url: URL endpoint streaming audio tren server.
        keywords: Danh sach tags cua bai hat.
    """

    id: str
    title: str
    artist: str | None
    duration: int
    duration_formatted: str
    thumbnail_url: str
    audio_url: str
    keywords: list[str]


class CompletedSongsListResponse(BaseModel):
    """Danh sach bai hat da hoan thanh tra ve cho frontend.

    Attributes:
        songs: Danh sach cac bai hat da hoan thanh.
        total: Tong so bai hat trong ket qua.
    """

    songs: list[CompletedSongResponse]
    total: int


class CompletedSongsQueryParams(BaseModel):
    """Tham so truy van cho endpoint danh sach bai hat hoan thanh.

    Attributes:
        limit: So luong bai hat tra ve (1-1000, mac dinh 100).
        key: Tu khoa tim kiem bai hat (fuzzy matching).
    """

    limit: int | None = Field(
        default=100, ge=1, le=1000,
        description="So luong bai hat tra ve (1-1000)",
    )
    key: str | None = Field(
        default=None,
        description="Tu khoa tim kiem bai hat (fuzzy matching)",
    )

    @field_validator('limit', mode='before')
    @classmethod
    def validate_limit(cls, v):
        """Chuan hoa limit: ep kieu, clamp trong khoang [1, 1000]."""
        if v is None:
            return 100
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                return 100
        if not isinstance(v, int):
            return 100
        if v < 1:
            return 1
        if v > 1000:
            return 1000
        return v

    @field_validator('key', mode='before')
    @classmethod
    def validate_key(cls, v):
        """Chuan hoa key: strip whitespace, chuyen chuoi rong thanh None."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            return v.strip()
        return None

class FavoriteRequest(BaseModel):
    """Du lieu dau vao de them bai hat vao muc Yeu thich.

    Attributes:
        song_id: YouTube video ID cua bai hat.
    """
    song_id: str

