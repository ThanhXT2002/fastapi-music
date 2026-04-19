"""Bang trung gian lien ket nguoi dung voi bai hat (many-to-many).

Lien quan:
- Model: user.py (User.id)
- Model: song.py (Song.id)
"""

# ── Third-party imports ───────────────────────────────────
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.config.database import Base

class UserSong(Base):
    __tablename__ = "user_songs"

    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    song_id = Column(String(50), ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_user_songs_created', 'created_at'),
    )
