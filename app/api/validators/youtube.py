from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class YouTubeInfoRequest(BaseModel):
    url: str = Field(..., min_length=1)
    
    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v):
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        if not re.search(youtube_regex, v):
            raise ValueError('Invalid YouTube URL')
        return v

class YouTubeInfoResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class YouTubeInfo(BaseModel):
    """Thông tin YouTube video cho Frontend"""
    title: str
    artist: str  # Channel name
    thumbnail_url: str
    duration: int  # in seconds
    video_id: str
    direct_audio_url: Optional[str] = None  # URL trực tiếp đến audio stream
    audio_format: Optional[str] = None  # m4a, webm, etc.
    quality: Optional[str] = None  # Audio quality info
