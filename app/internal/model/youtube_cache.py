from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.config.database import Base

class YouTubeCache(Base):
    """Cache cho YouTube videos đã được download và lưu trữ local server"""
    __tablename__ = "youtube_cache"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(20), unique=True, index=True, nullable=False)  # YouTube video ID
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)  # Original thumbnail URL from YouTube
    duration = Column(Integer, nullable=False)  # Duration in seconds
    duration_formatted = Column(String(20), nullable=True)  # mm:ss format
    keywords = Column(Text, nullable=True)  # JSON string of keywords
    
    # Original YouTube info
    original_url = Column(String(500), nullable=False)  # Original YouTube URL
    
    # Local server paths (không có domain, chỉ có path)
    audio_url = Column(String(500), nullable=False)  # Local audio file path on server (without domain)
    
    # Optional user tracking
    user_id = Column(Integer, nullable=True)  # Who first cached this video
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    def __repr__(self):
        return f"<YouTubeCache(video_id={self.video_id}, title={self.title})>"
    
    def get_keywords_list(self):
        """Parse keywords từ JSON string thành list"""
        if not self.keywords:
            return []
        try:
            import json
            return json.loads(self.keywords)
        except:
            return []