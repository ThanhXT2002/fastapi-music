import yt_dlp
import random
import time
from typing import Dict, Optional
from pathlib import Path
from app.config.config import settings
import os
import shutil
import subprocess
from pathlib import Path
import requests

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
    

    
    def download_audio_to_server(self, url: str, video_id: str = None) -> Dict:
        """Download YouTube audio to server as m4a file
        
        Args:
            url: YouTube video URL
            video_id: Optional video ID (if already extracted)
            
        Returns:
            Dict with success status, local audio path, and video info
        """
        try:
            # Validate URL
            if not self._is_valid_youtube_url(url):
                return {
                    "success": False,
                    "message": "Invalid YouTube URL"
                }
            
            # Extract video info first
            info = self.extract_info(url)
            if not info:
                return {
                    "success": False,
                    "message": "Failed to extract video information"
                }
            
            video_id = video_id or info.get('id', 'unknown')
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown Artist')
            
            # Create unique filename
            timestamp = int(time.time())
            filename = f"{video_id}_{timestamp}.m4a"
            output_path = self.audio_dir / filename
            
            # Ensure audio directory exists
            self.audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp for audio download
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_path.with_suffix('')),  # yt-dlp will add extension
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
                'ignoreerrors': False,
                'extractaudio': True,
                'audioformat': 'm4a',
                'audioquality': '192K',
            }
            
            print(f"Downloading audio to server: {title}")
            print(f"Output path: {output_path}")
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            # Download with yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check if file was created (yt-dlp might change the filename)
            expected_file = output_path.with_suffix('.m4a')
            
            # Find the actual downloaded file
            actual_file = None
            for file in self.audio_dir.glob(f"{video_id}_{timestamp}.*"):
                if file.suffix.lower() in ['.m4a', '.mp4', '.webm', '.mp3']:
                    actual_file = file
                    break
            
            if not actual_file or not actual_file.exists():
                return {
                    "success": False,
                    "message": "Download failed - output file not found"
                }
            
            # Rename to ensure .m4a extension
            if actual_file.suffix.lower() != '.m4a':
                final_file = actual_file.with_suffix('.m4a')
                actual_file.rename(final_file)
                actual_file = final_file
            
            # Verify file size
            file_size = actual_file.stat().st_size
            if file_size < 1024:  # Less than 1KB
                actual_file.unlink()
                return {
                    "success": False,
                    "message": "Download failed - file too small"
                }            # Get video metadata
            thumbnails = info.get('thumbnails', [])
            thumbnail_url = None  # Sẽ chứa đường dẫn local sau khi download
            
            if thumbnails:
                sorted_thumbnails = sorted(thumbnails, 
                                          key=lambda x: ((x.get('width') or 0) * (x.get('height') or 0)), 
                                          reverse=True)
                original_thumbnail_url = sorted_thumbnails[0].get('url') if sorted_thumbnails else None
                
                # Download thumbnail to server
                if original_thumbnail_url:
                    thumbnail_result = self.download_thumbnail_to_server(original_thumbnail_url, video_id)
                    if thumbnail_result["success"]:
                        thumbnail_url = thumbnail_result["local_thumbnail_path"]  # Sử dụng đường dẫn local
                        print(f"✓ Thumbnail saved: {thumbnail_url}")
                    else:
                        print(f"⚠ Failed to download thumbnail: {thumbnail_result['message']}")
                        thumbnail_url = original_thumbnail_url  # Fallback về URL gốc nếu download thất bại
            
            duration = info.get('duration', 0)
            tags = info.get('tags', [])
            categories = info.get('categories', [])
            keywords = tags + categories
            keywords = [k for k in keywords if k and k.strip()][:10]
            
            # Return local server path (without domain)
            local_audio_path = f"/audio/{actual_file.name}"
            
            result = {
                "success": True,
                "message": "Audio and thumbnail downloaded successfully",
                "video_data": {
                    "id": video_id,
                    "title": title,
                    "artist": uploader,
                    "thumbnail_url": thumbnail_url,  # Đường dẫn local hoặc URL gốc
                    "audio_url": local_audio_path,  # Local server path
                    "duration": duration,
                    "duration_formatted": self._format_duration(duration),
                    "keywords": keywords,
                    "original_url": url,
                    "file_size": file_size,
                    "local_file_path": str(actual_file)
                }
            }
            
            print(f"✓ Successfully downloaded: {local_audio_path}")
            print(f"  File size: {file_size / (1024*1024):.2f} MB")
            
            return result
            
        except yt_dlp.utils.DownloadError as e:
            return {
                "success": False,
                "message": f"yt-dlp download error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Download error: {str(e)}"
            }
    
    def download_thumbnail_to_server(self, thumbnail_url: str, video_id: str) -> Dict:
        """Download thumbnail to server
        
        Args:
            thumbnail_url: URL of the thumbnail image
            video_id: Video ID for filename
            
        Returns:
            Dict with success status and local thumbnail path
        """
        try:
            if not thumbnail_url:
                return {
                    "success": False,
                    "message": "No thumbnail URL provided"
                }
            
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
            
            # Ensure thumbnail directory exists
            self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            # Download thumbnail with requests
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            print(f"Downloading thumbnail: {thumbnail_url}")
            
            response = requests.get(thumbnail_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save thumbnail to file
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
            
            # Verify file was created and has content
            if not thumbnail_path.exists() or thumbnail_path.stat().st_size == 0:
                return {
                    "success": False,
                    "message": "Failed to save thumbnail file"
                }
            
            # Return local server path
            local_thumbnail_path = f"/thumbnails/{filename}"
            
            print(f"✓ Successfully downloaded thumbnail: {local_thumbnail_path}")
            print(f"  File size: {thumbnail_path.stat().st_size / 1024:.2f} KB")
            
            return {
                "success": True,
                "message": "Thumbnail downloaded successfully",
                "local_thumbnail_path": local_thumbnail_path,
                "local_file_path": str(thumbnail_path),
                "file_size": thumbnail_path.stat().st_size
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "message": f"Failed to download thumbnail: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Thumbnail download error: {str(e)}"
            }
    
    def get_domain_url(self, request) -> str:
        """Get domain URL automatically for ngrok or local development"""
        try:
            # Check if using ngrok
            forwarded_proto = request.headers.get('x-forwarded-proto')
            forwarded_host = request.headers.get('x-forwarded-host')
            
            if forwarded_proto and forwarded_host:
                return f"{forwarded_proto}://{forwarded_host}"
            
            # Fallback to request base URL
            base_url = str(request.base_url).rstrip('/')
            return base_url
        except:
            # Last resort fallback
            return "http://localhost:8000"