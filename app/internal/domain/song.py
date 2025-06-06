from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base
from app.internal.domain.user_songs import user_songs

class Song(Base):
    __tablename__ = "songs"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    duration = Column(Integer, nullable=False)  # in seconds

    thumbnail_url = Column(String(500), nullable=True)  
    audio_url = Column(String(500), nullable=True)     
    local_path = Column(String(500), nullable=True)
    
    # User interaction
    is_favorite = Column(Boolean, default=False)
    
    # Metadata
    keywords = Column(Text, nullable=True)  # JSON string of keywords array
    source_url = Column(String(500), nullable=True)  # Original source URL (YouTube, etc.)
    
    # User relationship - Many-to-many
    users = relationship("User", secondary=user_songs, back_populates="songs")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
