# filepath: e:\API\fastapi-music\app\api\validators\song.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime

class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    artists: Optional[List[str]] = None
    album: Optional[str] = None
    duration: int = Field(..., ge=0)  # Changed from gt=0 to ge=0 to allow 0 duration
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
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        # Handle case where keywords might be passed as a JSON string
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                # If it's not valid JSON, treat as a single keyword
                return [v] if v else []
        return v

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
