from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from app_v3.config.database import Base

class Song(Base):
    __tablename__ = "songs"
    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=False)
    thumbnail_url_cloudinary = Column(String(500), nullable=True)
    audio_url_cloudinary = Column(String(500), nullable=True)
    thumbnail_local_path = Column(String(500), nullable=True)
    audio_local_path = Column(String(500), nullable=True)
    is_favorite = Column(Boolean, default=False)
    keywords = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    status = Column(String(20), default="pending", nullable=False)
    audio_filename = Column(String(300), nullable=True)
    thumbnail_filename = Column(String(300), nullable=True)
    error_message = Column(Text, nullable=True)
    duration_formatted = Column(String(20), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
