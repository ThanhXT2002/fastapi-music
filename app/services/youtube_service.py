import yt_dlp
import asyncio
import aiofiles
import os
import json
import random
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import re
import uuid
import requests
from sqlalchemy.orm import Session

from app.models.song import SongV3, ProcessingStatus
from app.config.config import settings

class YouTubeService:
    def __init__(self):
        self.audio_dir = Path(settings.AUDIO_DIRECTORY)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIRECTORY)
        
        # Ensure directories exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # User agents pool để tránh bị detect
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def format_duration(self, duration_seconds: int) -> str:
        """Format duration from seconds to MM:SS"""
        if not duration_seconds:
            return "00:00"
        
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"        
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    async def get_video_info(self, url: str, quick_check: bool = False) -> Dict[str, Any]:
        """
        Get video information without downloading
        quick_check: Nếu True, sẽ giảm delay và timeout cho việc kiểm tra nhanh
        """
        # Reduced timeouts and delays for quick checks
        socket_timeout = 15 if quick_check else 30
        delay_range = (0.5, 1.5) if quick_check else (1, 3)
        
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
            'socket_timeout': socket_timeout,
            'retries': 2 if quick_check else 3,
            'nocheckcertificate': True,
        }
        
        def _extract_info():
            # Thêm delay ngẫu nhiên để tránh rate limiting
            time.sleep(random.uniform(*delay_range))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _extract_info)
        
        video_id = self.extract_video_id(url)
        if not video_id:
            video_id = info.get('id', str(uuid.uuid4()))
        
        # Extract thumbnail URL (prioritize high quality)
        thumbnail_url = info.get('thumbnail')
        if not thumbnail_url and 'thumbnails' in info:
            thumbnails = info['thumbnails']
            # Try to get best quality thumbnail
            sorted_thumbnails = sorted(thumbnails, 
                                     key=lambda x: ((x.get('width') or 0) * (x.get('height') or 0)), 
                                     reverse=True)
            if sorted_thumbnails:
                thumbnail_url = sorted_thumbnails[0].get('url')
        
        # Extract keywords/categories
        keywords = []
        tags = info.get('tags', [])
        categories = info.get('categories', [])
        if tags:
            keywords.extend(tags[:5])  # Limit to 5 tags
        if categories:
            keywords.extend(categories)
        if not keywords:
            keywords = ["Music"]
        
        return {
            'id': video_id,
            'title': info.get('title', 'Unknown Title'),
            'artist': info.get('uploader', 'Unknown Artist'),
            'thumbnail_url': thumbnail_url or '',
            'duration': int(info.get('duration', 0)),
            'duration_formatted': self.format_duration(int(info.get('duration', 0))),
            'keywords': keywords,
            'original_url': url,
        }
    
    async def download_thumbnail_to_server(self, thumbnail_url: str, video_id: str) -> Optional[str]:
        """Download thumbnail to server and return filename"""
        try:
            if not thumbnail_url:
                return None
            
            # Create unique filename for thumbnail
            timestamp = int(time.time())
            # Get file extension from URL or default to .jpg
            if thumbnail_url.endswith('.webp'):
                extension = '.webp'
            elif thumbnail_url.endswith('.png'):
                extension = '.png'
            else:
                extension = '.jpg'
            
            filename = f"{video_id}_{timestamp}{extension}"
            thumbnail_path = self.thumbnail_dir / filename
            
            def _download_thumbnail():
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                }
                
                response = requests.get(thumbnail_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Save thumbnail to file
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                return thumbnail_path.exists() and thumbnail_path.stat().st_size > 0
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _download_thumbnail)
            
            if success:
                return filename
            return None
            
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")
            return None
    
    async def download_audio_and_thumbnail(self, song_id: str, url: str, db: Session) -> bool:
        """Download audio and thumbnail files in background"""
        try:
            # Update status to processing
            song = db.query(SongV3).filter(SongV3.id == song_id).first()
            if not song:
                return False
            
            song.status = ProcessingStatus.PROCESSING
            db.commit()
            
            # Generate timestamp
            timestamp = int(time.time())
            
            def _download_audio():
                # Configure yt-dlp for audio download
                output_path = self.audio_dir / f"{song_id}_{timestamp}"  # No extension
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': str(output_path),  # yt-dlp will add extension automatically
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                        'preferredquality': '192',
                    }],
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
                    'socket_timeout': 60,
                    'retries': 3,
                    'nocheckcertificate': True,
                    'extractaudio': True,
                    'audioformat': 'm4a',
                    'audioquality': '192K',
                }
                
                # Add delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                # Download with yt-dlp
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Find the actual downloaded file - could be with or without extension
                actual_file = None
                
                # Check for files with this pattern
                for file in self.audio_dir.glob(f"{song_id}_{timestamp}*"):
                    if file.is_file():
                        # Prefer files with audio extensions
                        if file.suffix.lower() in ['.m4a', '.mp4', '.webm', '.mp3']:
                            actual_file = file
                            break
                        # But also accept files without extensions (yt-dlp sometimes does this)
                        elif not actual_file:
                            actual_file = file
                
                if actual_file and actual_file.exists():
                    # Verify file size
                    file_size = actual_file.stat().st_size
                    if file_size < 1024:  # Less than 1KB
                        actual_file.unlink()
                        return None
                    
                    # If file doesn't have .m4a extension, rename it
                    if actual_file.suffix.lower() != '.m4a':
                        final_file = actual_file.with_suffix('.m4a')
                        if final_file.exists():
                            final_file.unlink()  # Remove existing file if it exists
                        actual_file.rename(final_file)
                        actual_file = final_file
                    
                    return actual_file.name
                
                return None
            
            # Run download in thread pool
            loop = asyncio.get_event_loop()
            downloaded_audio_filename = await loop.run_in_executor(None, _download_audio)
            
            if not downloaded_audio_filename:
                raise Exception("Audio download failed")
            
            # Download thumbnail
            thumbnail_filename = await self.download_thumbnail_to_server(
                song.thumbnail_url, song_id
            )
            
            # Update database
            song.audio_filename = downloaded_audio_filename
            song.thumbnail_filename = thumbnail_filename
            song.status = ProcessingStatus.COMPLETED
            song.completed_at = datetime.utcnow()
            db.commit()
            
            return True
            
        except Exception as e:
            # Update status to failed
            if song:
                song.status = ProcessingStatus.FAILED
                song.error_message = str(e)
                db.commit()
            return False
