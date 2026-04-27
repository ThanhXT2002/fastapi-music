from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.config.database import Base

class Playlist(Base):
    """Bảng lưu trữ danh sách phát của người dùng."""
    __tablename__ = "playlists"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(String(36), index=True, nullable=False)  # Lưu Firebase UID
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Quan hệ
    songs = relationship("PlaylistSong", back_populates="playlist", cascade="all, delete-orphan", lazy="selectin")

class PlaylistSong(Base):
    """Bảng trung gian lưu trữ liên kết giữa Playlist và Bài hát."""
    __tablename__ = "playlist_songs"

    playlist_id = Column(String(36), ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True)
    song_id = Column(String(36), primary_key=True)  # YouTube ID
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    playlist = relationship("Playlist", back_populates="songs")
