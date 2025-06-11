from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime

class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    artist: str = Field(..., min_length=1, max_length=255)
    album: Optional[str] = None
    duration: int = Field(..., ge=0)  # Allow 0 duration
    
    thumbnail_url: Optional[str] = None
    audio_url: Optional[str] = None
    
    is_favorite: bool = Field(default=False)
    keywords: Optional[str] = None  # JSON string of keywords array
    source_url: Optional[str] = None  # Original source URL (YouTube, etc.)
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        # Handle case where keywords might be passed as a JSON string or list
        if v is None:
            return None
        if isinstance(v, str):
            try:
                import json
                json.loads(v)  # Just validate it's valid JSON
                return v
            except:
                # If it's not valid JSON, treat as a single keyword
                return json.dumps([v]) if v else None
        elif isinstance(v, list):
            import json
            return json.dumps(v)
        return v

class SongResponse(SongBase):
    id: str
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

class SimpleDownloadRequest(BaseModel):
    url: str = Field(..., min_length=1, description="YouTube URL to download")
    
    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v):
        import re
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        if not re.search(youtube_regex, v):
            raise ValueError('Invalid YouTube URL')
        return v

class YouTubeDownloadResponse(BaseModel):
    success: bool
    message: str
    song: Optional[SongResponse] = None
    download_path: Optional[str] = None

class VideoInfoResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class VideoInfoData(BaseModel):
    id: str
    title: Optional[str] = None
    artist: Optional[str] = None
    thumbnail_url: Optional[str] = None
    channel_avatar_url: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[int] = None
    duration_formatted: Optional[str] = None
    keywords: Optional[List[str]] = None
