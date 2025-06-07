import re  
from app.internal.utils.youtube_downloader import YouTubeDownloader
from app.api.validators.song import (
     VideoInfoResponse
)

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
                    message='Invalid YouTube URL format'
                )
                
            # Use the YouTubeDownloader's get_video_details method
            video_details = self.youtube_downloader.get_video_details(url)
            
            # Return a VideoInfoResponse object
            return video_details
                
        except Exception as e:
            print(f"Error in get_video_info: {e}")
            return VideoInfoResponse(
                success=False,
                message=f"Error getting video info: {str(e)}"
            )
            
   