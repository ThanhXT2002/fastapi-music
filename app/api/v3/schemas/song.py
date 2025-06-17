from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SongInfoRequest(BaseModel):
    youtube_url: str

class SongInfoResponse(BaseModel):
    id: str
    title: str
    artist: Optional[str]
    thumbnail_url: str
    duration: int
    duration_formatted: str
    keywords: List[str]
    original_url: str
    created_at: datetime

class StatusResponse(BaseModel):
    id: str
    status: ProcessingStatus
    progress: Optional[float] = None  # 0.0 to 1.0
    error_message: Optional[str] = None
    audio_filename: Optional[str] = None
    thumbnail_filename: Optional[str] = None
    updated_at: datetime

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
