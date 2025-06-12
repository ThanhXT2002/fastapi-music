from sqlalchemy.orm import Session
from typing import Optional, List
import json
import re
from app.internal.model.youtube_cache import YouTubeCache
from app.internal.storage.repositories.repository import BaseRepository

class YouTubeCacheRepository(BaseRepository[YouTubeCache]):
    def __init__(self, db: Session):
        super().__init__(YouTubeCache, db)
    
    def find_by_video_id(self, video_id: str) -> Optional[YouTubeCache]:
        """Tìm cache theo YouTube video ID"""
        return self.db.query(YouTubeCache).filter(
            YouTubeCache.video_id == video_id
        ).first()
    
    def find_by_url(self, url: str) -> Optional[YouTubeCache]:
        """Tìm cache theo YouTube URL"""
        video_id = self._extract_video_id(url)
        if not video_id:
            return None
        return self.find_by_video_id(video_id)
    def create_cache(self, video_data: dict, user_id: Optional[int] = None) -> YouTubeCache:
        """Tạo cache entry mới"""
        cache_data = {
            'video_id': video_data.get('id'),
            'title': video_data.get('title'),
            'artist': video_data.get('artist'),
            'thumbnail_url': video_data.get('thumbnail_url'),
            'duration': video_data.get('duration'),
            'duration_formatted': video_data.get('duration_formatted'),
            'keywords': json.dumps(video_data.get('keywords', [])),
            'original_url': video_data.get('original_url'),
            'audio_url': video_data.get('audio_url'),  # Local server path
            'user_id': user_id
        }
        
        cache_entry = YouTubeCache(**cache_data)
        self.db.add(cache_entry)
        self.db.commit()
        self.db.refresh(cache_entry)
        return cache_entry
    
    def get_recent_cached_videos(self, limit: int = 50) -> List[YouTubeCache]:
        """Lấy danh sách video gần đây đã cache"""
        return self.db.query(YouTubeCache).order_by(
            YouTubeCache.created_at.desc()
        ).limit(limit).all()
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID từ URL"""
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
