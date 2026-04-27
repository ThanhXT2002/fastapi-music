from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PlaylistCreate(BaseModel):
    """Schema dữ liệu đầu vào khi tạo Playlist mới"""
    id: str  # Lấy ID từ client sinh ra
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    coverUrl: Optional[str] = None
    isPublic: bool = False

class PlaylistTrackAdd(BaseModel):
    """Schema khi thêm track vào playlist"""
    trackId: str

class PlaylistResponse(BaseModel):
    """Schema trả về cho Playlist"""
    id: str
    title: str
    ownerId: str
    ownerName: str
    trackCount: int
    isPublic: bool
    createdAt: str
    updatedAt: str

    class Config:
        from_attributes = True
