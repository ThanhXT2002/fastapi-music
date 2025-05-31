from sqlalchemy.orm import Session
from typing import Optional
import json
import uuid
from app.internal.domain.song import Song
from app.internal.storage.repositories.repository import BaseRepository

class SongRepository(BaseRepository[Song]):
    def __init__(self, db: Session):
        super().__init__(Song, db)
    
    def create_song(self, song_data: dict, user_id: Optional[int] = None) -> Song:
        """Create a new song"""
        song_data['id'] = str(uuid.uuid4())
        song_data['user_id'] = user_id
        
        # Convert list fields to JSON strings
        if 'artists' in song_data and song_data['artists']:
            song_data['artists'] = json.dumps(song_data['artists'])
        if 'genre' in song_data and song_data['genre']:
            song_data['genre'] = json.dumps(song_data['genre'])
        if 'keywords' in song_data and song_data['keywords']:
            song_data['keywords'] = json.dumps(song_data['keywords'])
            
        return super().create(song_data)
    
    def find_by_youtube_url(self, url: str) -> Optional[Song]:
        """Find song by YouTube URL"""
        return self.db.query(Song).filter(Song.audio_url == url).first()
