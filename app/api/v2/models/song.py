from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from app.config.database import Base


class SongV2(Base):
    __tablename__ = "songs_v2"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String, nullable=True)
    duration = Column(Integer, nullable=False)  # seconds
    duration_formatted = Column(String, nullable=False)
    
    # Source info
    source = Column(String, nullable=False)  # "youtube"
    source_url = Column(String, nullable=False)
    
    # Processing status
    is_ready = Column(Boolean, default=False)
    is_processing = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # File paths (local storage)
    audio_file_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    
    # Metadata
    keywords = Column(Text, nullable=True)  # JSON array as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DownloadLogV2(Base):
    __tablename__ = "download_logs_v2"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
