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


