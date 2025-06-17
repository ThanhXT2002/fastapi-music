from pydantic import BaseModel
from typing import List, Optional


class Song(BaseModel):
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: int  # seconds
    duration_formatted: str  # "3:45"
    thumbnail_url: str
    available: bool  # Ready for download?
    source: str  # "youtube"
    keywords: List[str] = []


class SearchResponse(BaseModel):
    success: bool = True
    songs: List[Song]
    total: int


class FileInfo(BaseModel):
    size: int  # File size in bytes
    chunks: int  # Number of chunks (for files > 5MB)
    chunk_size: int = 1048576  # 1MB chunks
    checksum: str  # Simple MD5 hash


class DownloadInfo(BaseModel):
    song_id: str
    ready: bool
    processing: bool = False
    error: Optional[str] = None
    
    # Only if ready = True
    audio_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_info: Optional[FileInfo] = None


class ProcessRequest(BaseModel):
    song_url: str  # YouTube URL or other source
    quality: str = "medium"  # low, medium, high


class ProcessResponse(BaseModel):
    success: bool
    message: str
    song_id: Optional[str] = None
    status: str  # "queued", "processing", "completed", "failed"


class DownloadEvent(BaseModel):
    song_id: str
    event_type: str  # "started", "completed", "failed"
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None
