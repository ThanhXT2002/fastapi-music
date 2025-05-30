from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
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
    
    def find_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Song]:
        """Get all songs for a user"""
        return self.db.query(Song).filter(
            Song.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def find_favorites_by_user(self, user_id: int) -> List[Song]:
        """Get favorite songs for a user"""
        return self.db.query(Song).filter(
            and_(Song.user_id == user_id, Song.is_favorite == True)
        ).all()
    
    def find_by_source(self, source: str, user_id: Optional[int] = None) -> List[Song]:
        """Get songs by source (youtube, local, spotify)"""
        query = self.db.query(Song).filter(Song.source == source)
        if user_id:
            query = query.filter(Song.user_id == user_id)
        return query.all()
    
    def search_songs(self, query: str, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Song]:
        """Search songs by title, artist, or album"""
        search_filter = or_(
            Song.title.ilike(f"%{query}%"),
            Song.artist.ilike(f"%{query}%"),
            Song.album.ilike(f"%{query}%")
        )
        
        db_query = self.db.query(Song).filter(search_filter)
        if user_id:
            db_query = db_query.filter(Song.user_id == user_id)
            
        return db_query.offset(skip).limit(limit).all()
    
    def update_play_count(self, song_id: str) -> Song:
        """Increment play count and update last played time"""
        song = self.find_by_id(song_id)
        if song:
            song.play_count += 1
            from datetime import datetime
            song.last_played_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(song)
        return song
    
    def toggle_favorite(self, song_id: str) -> Song:
        """Toggle favorite status of a song"""
        song = self.find_by_id(song_id)
        if song:
            song.is_favorite = not song.is_favorite
            self.db.commit()
            self.db.refresh(song)
        return song
    
    def find_by_youtube_url(self, url: str) -> Optional[Song]:
        """Find song by YouTube URL"""
        return self.db.query(Song).filter(Song.audio_url == url).first()
    
    def get_recently_played(self, user_id: int, limit: int = 10) -> List[Song]:
        """Get recently played songs"""
        return self.db.query(Song).filter(
            and_(Song.user_id == user_id, Song.last_played_at.isnot(None))
        ).order_by(desc(Song.last_played_at)).limit(limit).all()
    
    def bulk_create_songs(self, songs_data: List[dict], user_id: int) -> List[Song]:
        """Create multiple songs at once"""
        created_songs = []
        for song_data in songs_data:
            try:
                song = self.create_song(song_data, user_id)
                created_songs.append(song)
            except Exception as e:
                # Log error but continue with other songs
                print(f"Error creating song: {e}")
                continue
        return created_songs
