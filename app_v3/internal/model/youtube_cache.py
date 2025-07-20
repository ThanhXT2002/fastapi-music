from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app_v3.config.database import Base

class YouTubeCache(Base):
    __tablename__ = "youtube_cache"
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=True)
    audio_filename = Column(String(300), nullable=True)
    thumbnail_filename = Column(String(300), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
