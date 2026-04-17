"""Bang trung gian lien ket nguoi dung voi bai hat (many-to-many).

Lien quan:
- Model: user.py (User.id)
- Model: song.py (Song.id)
"""

# ── Third-party imports ───────────────────────────────────
from sqlalchemy import Table, Column, Integer, ForeignKey

# ── Internal imports ──────────────────────────────────────
from app.config.database import Base

user_songs = Table(
    "user_songs",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("song_id", Integer, ForeignKey("songs.id")),
)
