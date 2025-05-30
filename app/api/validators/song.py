from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re

class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    artists: Optional[List[str]] = None
    album: Optional[str] = None
    duration: int = Field(..., gt=0)
    genre: Optional[List[str]] = None
    release_date: Optional[str] = None
    
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    lyrics: Optional[str] = None
    has_lyrics: Optional[bool] = False
    
    keywords: Optional[List[str]] = None
    source: Optional[str] = Field(default='youtube')
    bitrate: Optional[int] = None
    language: Optional[str] = None
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if v not in ['local', 'youtube', 'spotify']:
            raise ValueError('Source must be one of: local, youtube, spotify')
        return v

class SongCreate(SongBase):
    pass

class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    artists: Optional[List[str]] = None
    album: Optional[str] = None
    duration: Optional[int] = None
    genre: Optional[List[str]] = None
    release_date: Optional[str] = None
    
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    lyrics: Optional[str] = None
    has_lyrics: Optional[bool] = None
    
    is_favorite: Optional[bool] = None
    keywords: Optional[List[str]] = None
    bitrate: Optional[int] = None
    language: Optional[str] = None

class SongResponse(SongBase):
    id: str
    is_downloaded: bool
    downloaded_at: Optional[datetime]
    local_path: Optional[str]
    
    is_favorite: bool
    play_count: int
    last_played_at: Optional[datetime]
    
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class YouTubeDownloadRequest(BaseModel):
    url: str = Field(..., min_length=1)
    download_audio: bool = Field(default=True)
    quality: str = Field(default='best')
    
    @field_validator('quality')
    @classmethod
    def validate_quality(cls, v):
        if v not in ['best', 'worst', 'bestaudio', 'worstaudio']:
            raise ValueError('Quality must be one of: best, worst, bestaudio, worstaudio')
        return v

class YouTubeDownloadResponse(BaseModel):
    success: bool
    message: str
    song: Optional[SongResponse] = None
    download_path: Optional[str] = None

class SongSyncRequest(BaseModel):
    songs: List[SongCreate]

class SongSyncResponse(BaseModel):
    success: bool
    message: str
    synced_count: int
    failed_count: int
    errors: Optional[List[str]] = None
