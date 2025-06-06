from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from app.config.database import Base

# Bảng trung gian để liên kết users và songs (many-to-many)
user_songs = Table(
    "user_songs",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("song_id", String(36), ForeignKey("songs.id")),
    Column("created_at", DateTime(timezone=True), server_default=func.now())
)
