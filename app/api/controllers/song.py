import re  
from app.internal.utils.youtube_downloader import YouTubeDownloader
from app.internal.utils.youtube_service import YouTubeService
from app.api.validators.song import (
     VideoInfoResponse
)
from fastapi import Request
from sqlalchemy.orm import Session
from typing import Optional

class SongController:
    def __init__(self):
        self.youtube_downloader = YouTubeDownloader()
            
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL format"""
        youtube_patterns = [
            r'(?:https?://)(?:www\.)?youtube\.com/watch\?v=[\w\-]{11}',
            r'(?:https?://)(?:www\.)?youtu\.be/[\w\-]{11}',
            r'(?:https?://)(?:www\.)?youtube\.com/embed/[\w\-]{11}',
            r'(?:https?://)(?:www\.)?youtube\.com/v/[\w\-]{11}',        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    
    def get_video_info(self, url: str):
        """Get video information without downloading
        
        Returns:
            VideoInfoResponse object containing video details
        """
        try:
            if not self._is_valid_youtube_url(url):
                return VideoInfoResponse(
                    success=False,
                    message='Invalid YouTube URL format',
                    data=None
                )
                
            # Use the YouTubeDownloader's get_video_details method
            video_details = self.youtube_downloader.get_video_details(url)
            
            # Assuming video_details returns a dict with video information
            return VideoInfoResponse(
                success=True,
                message="Video information retrieved successfully",
                data=video_details
            )
                
        except Exception as e:
            print(f"Error in get_video_info: {e}")
            return VideoInfoResponse(
                success=False,
                message=f"Error getting video info: {str(e)}",
                data=None
            )
    
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

