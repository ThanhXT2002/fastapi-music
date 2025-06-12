from typing import Dict, Optional
from sqlalchemy.orm import Session
from fastapi import Request
from app.internal.storage.repositories.youtube_cache import YouTubeCacheRepository
from app.internal.utils.youtube_downloader import YouTubeDownloader
import re

class YouTubeService:
    def __init__(self, db: Session):
        self.db = db
        self.cache_repo = YouTubeCacheRepository(db)
        self.downloader = YouTubeDownloader()
    
    def process_youtube_url(self, url: str, request: Request, user_id: Optional[int] = None) -> Dict:
        """
        Process YouTube URL with new workflow:
        1. Check if URL exists in cache
        2. If exists, return cached response
        3. If not exists, download audio to server
        4. Save to database cache
        5. Return response with full domain URL
        """
        try:
            # Validate YouTube URL
            if not self._is_valid_youtube_url(url):
                return {
                    "success": False,
                    "message": "Invalid YouTube URL"
                }
            
            # Extract video ID
            video_id = self._extract_video_id(url)
            if not video_id:
                return {
                    "success": False,
                    "message": "Could not extract video ID from URL"
                }
            
            # Check cache first
            cached_video = self.cache_repo.find_by_video_id(video_id)
            if cached_video:
                print(f"Found cached video: {cached_video.title}")
                return self._format_cached_response(cached_video, request)
            
            # Not in cache, download to server
            print(f"Video not in cache, downloading: {video_id}")
            download_result = self.downloader.download_audio_to_server(url, video_id)
            
            if not download_result.get("success"):
                return download_result
            
            # Save to cache database
            video_data = download_result["video_data"]
            cache_entry = self.cache_repo.create_cache(video_data, user_id)
            
            # Return response with full domain URL
            return self._format_new_response(cache_entry, request)
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing YouTube URL: {str(e)}"
            }
    
    def _format_cached_response(self, cached_video, request: Request) -> Dict:
        """Format response for cached video"""
        domain = self.downloader.get_domain_url(request)
        
        return {
            "success": True,
            "message": "Video found in cache",
            "cached": True,
            "data": {
                "id": cached_video.video_id,
                "title": cached_video.title,
                "artist": cached_video.artist,
                "thumbnail_url": cached_video.thumbnail_url,
                "audio_url": f"{domain}{cached_video.audio_url}",  # Full URL with domain
                "duration": cached_video.duration,
                "duration_formatted": cached_video.duration_formatted,
                "keywords": cached_video.get_keywords_list(),
                "original_url": cached_video.original_url,
                "created_at": cached_video.created_at.isoformat() if cached_video.created_at else None
            }
        }
    
    def _format_new_response(self, cache_entry, request: Request) -> Dict:
        """Format response for newly downloaded video"""
        domain = self.downloader.get_domain_url(request)
        
        return {
            "success": True,
            "message": "Video downloaded and cached successfully",
            "cached": False,
            "data": {
                "id": cache_entry.video_id,
                "title": cache_entry.title,
                "artist": cache_entry.artist,
                "thumbnail_url": cache_entry.thumbnail_url,
                "audio_url": f"{domain}{cache_entry.audio_url}",  # Full URL with domain
                "duration": cache_entry.duration,
                "duration_formatted": cache_entry.duration_formatted,
                "keywords": cache_entry.get_keywords_list(),
                "original_url": cache_entry.original_url,
                "created_at": cache_entry.created_at.isoformat() if cache_entry.created_at else None
            }
        }
    
    def get_recent_downloads(self, limit: int = 50) -> Dict:
        """Get recent downloaded videos from cache"""
        try:
            cached_videos = self.cache_repo.get_recent_cached_videos(limit)
            
            return {
                "success": True,
                "data": [
                    {
                        "id": video.video_id,
                        "title": video.title,
                        "artist": video.artist,
                        "thumbnail_url": video.thumbnail_url,
                        "audio_url": video.audio_url,  # Local path only
                        "duration": video.duration,
                        "duration_formatted": video.duration_formatted,
                        "keywords": video.get_keywords_list(),
                        "original_url": video.original_url,
                        "created_at": video.created_at.isoformat() if video.created_at else None
                    }
                    for video in cached_videos
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error fetching recent downloads: {str(e)}"
            }
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate if URL is a valid YouTube URL"""
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be',
            'm.youtube.com', 'music.youtube.com'
        ]
        return any(domain in url for domain in youtube_domains)
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
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
