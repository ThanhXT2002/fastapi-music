from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    artists = Column(Text, nullable=True)  # JSON string of artists array
    album = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=False)  # in seconds
    genre = Column(Text, nullable=True)  # JSON string of genres array
    release_date = Column(String(50), nullable=True)
    
    # Media files
    thumbnail_url = Column(String(500), nullable=True)
    audio_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    
    # Lyrics
    lyrics = Column(Text, nullable=True)
    has_lyrics = Column(Boolean, default=False)
    
    # Download info
    is_downloaded = Column(Boolean, default=False)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # User interaction
    is_favorite = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    last_played_at = Column(DateTime(timezone=True), nullable=True)
      # Metadata
    keywords = Column(Text, nullable=True)  # JSON string of keywords array
    source = Column(String(50), default='youtube')  # 'local', 'youtube', 'spotify'
    source_url = Column(String(500), nullable=True)  # Original source URL (YouTube, etc.)
    bitrate = Column(Integer, nullable=True)
    language = Column(String(10), nullable=True)
    
    # User relationship
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="songs")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
