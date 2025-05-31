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
            
    def get_video_details(self, url: str) -> Dict:
        """Get only necessary video details for frontend without downloading
        
        Returns:
            Dict with: title, artist, thumbnail_url, audio_url, duration
        """
        try:
            # Extract all info first
            info = self.extract_info(url)
            if not info:
                return {
                    "success": False,
                    "message": "Failed to extract video information"
                }
            
            # Get title and uploader (artist)
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown Artist')
            
            # Try to parse artist and title from video title (if it follows "Artist - Title" format)
            artist = uploader
            original_title = title
            if ' - ' in title:
                parts = title.split(' - ', 1)
                artist = parts[0].strip()
                title = parts[1].strip()
            
            # Get best thumbnail
            thumbnails = info.get('thumbnails', [])
            best_thumbnail = None
            if thumbnails:
                # Sort by resolution and pick the highest quality
                sorted_thumbnails = sorted(thumbnails, 
                                          key=lambda x: (x.get('width', 0) * x.get('height', 0)), 
                                          reverse=True)
                best_thumbnail = sorted_thumbnails[0].get('url') if sorted_thumbnails else None
            
            # Get direct audio stream URL
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            
            best_audio_url = None
            if audio_formats:
                # Sort by quality and pick the best
                sorted_formats = sorted(audio_formats,
                                       key=lambda x: x.get('abr', 0),
                                       reverse=True)
                best_audio_url = sorted_formats[0].get('url') if sorted_formats else None
            
            # If no audio-only format found, use the original URL
            if not best_audio_url:
                best_audio_url = url
            
            # Get duration
            duration = info.get('duration', 0)
            
            result = {
                "success": True,
                "title": title,
                "original_title": original_title,
                "artist": artist,
                "thumbnail_url": best_thumbnail,
                "audio_url": best_audio_url,
                "duration": duration,
                "duration_formatted": self._format_duration(duration)
            }
            
            return result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
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
    
    def download_audio(self, url: str, filename: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
        """Download audio from YouTube URL"""
        try:
            # Generate unique filename if not provided
            if not filename:
                filename = str(uuid.uuid4())
            
            audio_path = self.audio_dir / f"{filename}.%(ext)s"
            thumbnail_path = self.thumbnail_dir / f"{filename}.%(ext)s"            # Get FFmpeg path - improved detection
            ffmpeg_location = self._get_ffmpeg_location()
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(audio_path),
                'writethumbnail': True,
                'writeinfojson': False,
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
            
            # Add FFmpeg location if found
            if ffmpeg_location:
                ydl_opts['ffmpeg_location'] = ffmpeg_location
            
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
                  # Find thumbnail file and move it to correct directory
                thumbnail_file = None
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    potential_thumb = self.audio_dir / f"{filename}.{ext}"
                    if potential_thumb.exists():
                        # Move thumbnail to thumbnail directory
                        target_thumb = self.thumbnail_dir / f"{filename}.{ext}"
                        potential_thumb.rename(target_thumb)
                        thumbnail_file = target_thumb
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
    
    def _get_ffmpeg_location(self) -> Optional[str]:
        """Find FFmpeg location, always prioritize project ffmpeg/bin first"""
        import os
        import shutil
        import subprocess
        from pathlib import Path

        # Always prioritize ffmpeg in project root first
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        project_ffmpeg = project_root / "ffmpeg" / "bin"
        ffmpeg_exe = project_ffmpeg / "ffmpeg.exe"
        
        if ffmpeg_exe.exists():
            print(f"Using project ffmpeg: {project_ffmpeg}")
            return str(project_ffmpeg)

        # Fallback: try to find ffmpeg in PATH
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            print(f"Using system ffmpeg: {os.path.dirname(ffmpeg_path)}")
            return os.path.dirname(ffmpeg_path)

        # Last resort: try other common locations
        possible_paths = [
            os.path.join(os.getcwd(), "ffmpeg", "bin"),
            f"C:\\ffmpeg\\bin",
            "C:\\Program Files\\ffmpeg\\bin",
            "C:\\Program Files (x86)\\ffmpeg\\bin"
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "ffmpeg.exe")):
                print(f"Using fallback ffmpeg: {path}")
                return path

        print("FFmpeg not found in any location")
        return None