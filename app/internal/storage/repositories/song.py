from sqlalchemy.orm import Session
from typing import Optional
import json
import uuid
from app.internal.model.song import Song
from app.internal.storage.repositories.repository import BaseRepository

class SongRepository(BaseRepository[Song]):
    def __init__(self, db: Session):
        super().__init__(Song, db)
    
    def create_song(self, song_data: dict, user_id: Optional[int] = None) -> Song:
        """Create a new song"""
        song_data['id'] = str(uuid.uuid4())
        
        # Convert keywords to JSON string if it's a list
        if 'keywords' in song_data and isinstance(song_data['keywords'], list):
            song_data['keywords'] = json.dumps(song_data['keywords'])
            
        # Create song without user_id since we're using many-to-many relationship
        song = super().create(song_data)
        
        # If user_id is provided, create the relationship
        if user_id:
            from app.internal.model.user import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                song.users.append(user)
                self.db.commit()
                self.db.refresh(song)
        
        return song
    
    def find_by_youtube_url(self, url: str) -> Optional[Song]:
        """Find song by YouTube video ID extracted from URL with retry logic"""
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return None
        
        # Retry logic for database queries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Tìm bài hát có source_url chứa video_id
                from sqlalchemy import or_
                result = self.db.query(Song).filter(
                    Song.source_url.like(f"%{video_id}%")
                ).first()
                return result
            except Exception as e:
                print(f"Database query attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    # Reconnect database session
                    self.db.rollback()
                    continue
                else:
                    raise e
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        import re
        
        # Các pattern phổ biến cho YouTube URL
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    def update_song_cloudinary_urls(self, song_id: str, update_data: dict) -> Optional[Song]:
        """Update song with Cloudinary URLs"""
        try:
            song = self.find_by_id(song_id)
            if not song:
                print(f"❌ Song not found with ID: {song_id}")
                return None
            
            print(f"🔍 Found song: {song.title} (ID: {song_id})")
            print(f"🔄 Updating fields: {list(update_data.keys())}")
            
            # Update with new Cloudinary URLs
            for field, value in update_data.items():
                if hasattr(song, field):
                    old_value = getattr(song, field, None)
                    setattr(song, field, value)
                    print(f"✅ Updated {field}: {old_value} -> {value}")
                else:
                    print(f"⚠️ Field {field} not found in Song model")
            
            self.db.commit()
            self.db.refresh(song)
            print(f"✅ Database updated successfully for song: {song_id}")
            return song
            
        except Exception as e:
            print(f"❌ Error updating song cloudinary URLs: {e}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return None
