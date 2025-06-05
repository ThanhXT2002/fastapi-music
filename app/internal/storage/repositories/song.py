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
        """Find song by YouTube video ID extracted from URL"""
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return None
        
        # Tìm bài hát có source_url chứa video_id
        from sqlalchemy import or_
        return self.db.query(Song).filter(
            Song.source_url.like(f"%{video_id}%")
        ).first()

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        import re
        
        # Các mẫu regex cho các định dạng URL khác nhau
        patterns = [
            r'(?:v=|\/)([\w\-]{11})(?:[&#?]|$)',  # youtube.com/watch?v=ID
            r'(?:youtu\.be\/)([\w\-]{11})(?:[&#?]|$)',  # youtu.be/ID
            r'(?:embed\/)([\w\-]{11})(?:[&#?]|$)'  # youtube.com/embed/ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
