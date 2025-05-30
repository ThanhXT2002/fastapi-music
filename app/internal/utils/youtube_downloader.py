import yt_dlp
import os
import json
import uuid
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from app.config.config import settings

class YouTubeDownloader:
    def __init__(self):
        self.audio_dir = Path(settings.AUDIO_DIRECTORY)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIRECTORY)
        
        # Create directories if they don't exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_info(self, url: str) -> Optional[Dict]:
        """Extract video information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"Error extracting info: {e}")
            return None
    
    def download_audio(self, url: str, filename: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
        """Download audio from YouTube URL"""
        try:
            # Generate unique filename if not provided
            if not filename:
                filename = str(uuid.uuid4())
            
            audio_path = self.audio_dir / f"{filename}.%(ext)s"
            thumbnail_path = self.thumbnail_dir / f"{filename}.%(ext)s"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(audio_path),
                'writethumbnail': True,
                'writeinfojson': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'postprocessor_args': [
                    '-ar', '44100'
                ],
                'prefer_ffmpeg': True,
                'keepvideo': False,
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': 192,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                # Download
                ydl.download([url])
                
                # Get actual downloaded file paths
                audio_file = self.audio_dir / f"{filename}.mp3"
                info_file = self.audio_dir / f"{filename}.info.json"
                
                # Read additional info from json file if exists
                additional_info = {}
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        additional_info = json.load(f)
                
                # Find thumbnail file
                thumbnail_file = None
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    potential_thumb = self.audio_dir / f"{filename}.{ext}"
                    if potential_thumb.exists():
                        thumbnail_file = potential_thumb
                        break
                
                # Prepare song data
                song_data = self._extract_song_data(info, str(audio_file), str(thumbnail_file) if thumbnail_file else None)
                
                return True, str(audio_file), song_data
                
        except Exception as e:
            return False, f"Download failed: {str(e)}", None
    
    def _extract_song_data(self, info: Dict, audio_path: str, thumbnail_path: Optional[str] = None) -> Dict:
        """Extract song data from YouTube info"""
        # Extract duration in seconds
        duration = info.get('duration', 0)
        
        # Extract artist and title
        title = info.get('title', 'Unknown')
        uploader = info.get('uploader', 'Unknown')
        
        # Try to parse artist and title from video title
        artist = uploader
        if ' - ' in title:
            parts = title.split(' - ', 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        
        # Extract other metadata
        description = info.get('description', '')
        upload_date = info.get('upload_date', '')
        view_count = info.get('view_count', 0)
        
        # Format upload date
        release_date = None
        if upload_date:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(upload_date, '%Y%m%d')
                release_date = date_obj.strftime('%Y-%m-%d')
            except:
                release_date = upload_date
        
        # Extract tags/keywords
        tags = info.get('tags', [])
        categories = info.get('categories', [])
        keywords = tags + categories
        
        song_data = {
            'title': title,
            'artist': artist,
            'duration': duration,
            'release_date': release_date,
            'audio_url': info.get('webpage_url'),
            'local_path': audio_path,
            'thumbnail_url': thumbnail_path,
            'keywords': keywords[:10] if keywords else [],  # Limit to 10 keywords
            'source': 'youtube',
            'is_downloaded': True,
            'has_lyrics': False,  # Could be enhanced to extract lyrics
        }
        
        return song_data
    
    def get_playlist_info(self, url: str) -> Optional[Dict]:
        """Get playlist information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"Error extracting playlist info: {e}")
            return None
    
    def download_playlist(self, url: str, max_downloads: int = 10) -> List[Tuple[bool, str, Optional[Dict]]]:
        """Download multiple videos from playlist"""
        playlist_info = self.get_playlist_info(url)
        if not playlist_info or 'entries' not in playlist_info:
            return []
        
        results = []
        entries = playlist_info['entries'][:max_downloads]  # Limit downloads
        
        for entry in entries:
            if entry and entry.get('url'):
                video_url = entry.get('url')
                if not video_url.startswith('http'):
                    video_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                
                result = self.download_audio(video_url)
                results.append(result)
        
        return results
