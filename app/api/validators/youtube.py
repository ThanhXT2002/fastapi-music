from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class YouTubeDownloadRequest(BaseModel):
    """Request để download YouTube audio về server"""
    url: str = Field(..., min_length=1, description="YouTube video URL")
    
    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v):
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        if not re.search(youtube_regex, v):
            raise ValueError('Invalid YouTube URL')
        return v

class YouTubeDownloadResponse(BaseModel):
    """Response cho YouTube download"""
    success: bool
    message: str
    cached: Optional[bool] = None  # True nếu lấy từ cache, False nếu download mới
    data: Optional[dict] = None

class RecentDownloadsResponse(BaseModel):
    """Response cho recent downloads"""
    success: bool
    message: Optional[str] = None
    data: list = []
