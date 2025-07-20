from sqlalchemy import Table, Column, Integer, ForeignKey
from app.config.database import Base

user_songs = Table(
    "user_songs",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("song_id", Integer, ForeignKey("songs.id"))
)
