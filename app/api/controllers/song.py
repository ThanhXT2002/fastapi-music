import re  
from app.internal.utils.youtube_service import YouTubeService
from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional

class SongController:
    def __init__(self):
        pass
    
    def download_youtube_audio(self, url: str, request: Request, db: Session, user_id: Optional[int] = None):
        """
        Download YouTube audio với workflow mới:
        1. Kiểm tra cache trong SQLite
        2. Nếu có thì trả về response luôn
        3. Nếu không có thì download về server
        4. Lưu vào database và trả về response với full domain URL
        """
        try:
            youtube_service = YouTubeService(db)
            result = youtube_service.process_youtube_url(url, request, user_id)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Error downloading YouTube audio: {str(e)}"
            }
    
    def get_recent_downloads(self, db: Session, limit: int = 50):
        """Lấy danh sách video đã download gần đây"""
        try:
            youtube_service = YouTubeService(db)
            return youtube_service.get_recent_downloads(limit)
        except Exception as e:
            return {
                "success": False,
                "message": f"Error fetching recent downloads: {str(e)}"
            }

