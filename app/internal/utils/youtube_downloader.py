import yt_dlp
import random
import time
from typing import Dict, Optional
from pathlib import Path
from app.config.config import settings

class YouTubeDownloader:
    def __init__(self):
        self.audio_dir = Path(settings.AUDIO_DIRECTORY)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIRECTORY)
        
        # Create directories if they don't exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # User agents pool để tránh bị detect
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
    def extract_info(self, url: str) -> Optional[Dict]:
        """Extract video information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': random.choice(self.user_agents),
            'http_headers': {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Keep-Alive': '300',
                'Connection': 'keep-alive',
            },
            'socket_timeout': 30,
            'retries': 3,
            # Thêm các options để tránh bị chặn
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_color': True,
        }
        
        try:
            # Thêm delay ngẫu nhiên để tránh rate limiting
            time.sleep(random.uniform(1, 3))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except yt_dlp.utils.DownloadError as e:
            print(f"yt-dlp Download Error: {e}")
            return None
        except Exception as e:
            print(f"Error extracting info: {e}")
            return None
            
    def get_video_details(self, url: str) -> Dict:
        """Get only necessary video details for frontend without downloading
        
        Returns:
            Dict with: title, artist, thumbnail_url, audio_url, duration
        """
        try:
            # Validate URL trước khi process
            if not self._is_valid_youtube_url(url):
                return {
                    "success": False,
                    "message": "Invalid YouTube URL"
                }
            
            # Extract all info first
            info = self.extract_info(url)
            if not info:
                return {
                    "success": False,
                    "message": "Failed to extract video information - Video might be private, restricted, or unavailable"
                }
                
            # Get title and uploader (artist)
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown Artist')
            # Use uploader (channel name) as artist, keep original title unchanged
            artist = uploader
            # Don't modify title - keep it as is from YouTube
            
            # Get best thumbnail
            thumbnails = info.get('thumbnails', [])
            best_thumbnail = None
            if thumbnails:
                # Sort by resolution and pick the highest quality
                sorted_thumbnails = sorted(thumbnails, 
                                          key=lambda x: ((x.get('width') or 0) * (x.get('height') or 0)), 
                                          reverse=True)
                best_thumbnail = sorted_thumbnails[0].get('url') if sorted_thumbnails else None
            
            # Get direct audio stream URL với error handling tốt hơn
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            best_audio_url = None
            if audio_formats:
                # Sort by quality and pick the best
                sorted_formats = sorted(audio_formats,
                                       key=lambda x: x.get('abr') or 0,
                                       reverse=True)
                best_audio_url = sorted_formats[0].get('url') if sorted_formats else None
            
            # Fallback strategy nếu không tìm được audio-only format
            if not best_audio_url:
                # Tìm format có audio tốt nhất
                all_formats = [f for f in formats if f.get('acodec') != 'none']
                if all_formats:
                    sorted_all = sorted(all_formats,
                                       key=lambda x: (x.get('abr') or 0, x.get('height') or 0),
                                       reverse=True)
                    best_audio_url = sorted_all[0].get('url') if sorted_all else url
                else:
                    best_audio_url = url
                    
            # Get duration
            duration = info.get('duration', 0)
            
            # Extract keywords from tags and categories
            tags = info.get('tags', [])
            categories = info.get('categories', [])
            keywords = tags + categories
            # Limit to first 10 keywords and filter out empty ones
            keywords = [k for k in keywords if k and k.strip()][:10]
            
            result = {
                "title": title,
                "artist": artist,
                "thumbnail_url": best_thumbnail,
                "audio_url": best_audio_url,
                "duration": duration,
                "duration_formatted": self._format_duration(duration),
                "keywords": keywords
            }
            
            return result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate if URL is a valid YouTube URL"""
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be',
            'm.youtube.com', 'music.youtube.com'
        ]
        return any(domain in url for domain in youtube_domains)
    
    def _format_duration(self, seconds: int) -> str:
        """Format seconds into mm:ss or hh:mm:ss"""
        if not seconds:
            return "00:00"
        
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"