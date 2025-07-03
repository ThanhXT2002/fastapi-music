from pydantic import BaseModel, HttpUrl, Field, validator
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

class CompletedSongResponse(BaseModel):
    """Response schema for completed songs with streaming URLs"""
    id: str
    title: str
    artist: Optional[str]
    duration: int
    duration_formatted: str
    thumbnail_url: str  # URL để streaming thumbnail từ server
    audio_url: str      # URL để streaming audio
    keywords: List[str]

class CompletedSongsListResponse(BaseModel):
    """Response schema for list of completed songs"""
    songs: List[CompletedSongResponse]
    total: int

class CompletedSongsQueryParams(BaseModel):
    """Query parameters for completed songs endpoint"""
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Number of songs to return (1-1000)")
    
    @validator('limit', pre=True)
    def validate_limit(cls, v):
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
