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
                
            video_id = info.get('id', 'Unknown ID')
            
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
                best_thumbnail = sorted_thumbnails[0].get('url') if sorted_thumbnails else None            # Get direct audio stream URL với multiple strategies
            formats = info.get('formats', [])
            best_audio_url = None
              # Strategy 1: Lấy tất cả audio formats (bao gồm cả HLS)
            all_audio_formats = [f for f in formats 
                               if f.get('vcodec') == 'none' 
                               and f.get('acodec') != 'none']
            
            print(f"Found {len(all_audio_formats)} audio-only formats")
            
            # Tìm direct audio stream trước (không phải HLS)
            direct_audio_formats = [f for f in all_audio_formats 
                                  if not self._is_hls_url(f.get('url', ''))]
            
            if direct_audio_formats:
                print(f"Found {len(direct_audio_formats)} direct audio streams")
                # Ưu tiên các format phổ biến
                preferred_exts = ['webm', 'm4a', 'mp4', 'mp3']
                def format_priority(f):
                    ext = f.get('ext', '')
                    abr = f.get('abr') or 0
                    ext_priority = preferred_exts.index(ext) if ext in preferred_exts else 999
                    return (ext_priority, -abr)
                
                sorted_formats = sorted(direct_audio_formats, key=format_priority)
                best_audio_url = sorted_formats[0].get('url')
                print(f"Using direct audio stream: {sorted_formats[0].get('ext')} - {sorted_formats[0].get('abr')}kbps")
            else:
                # Strategy 2: Không có direct stream, bắt buộc convert HLS
                print("No direct audio streams found. All audio formats are HLS - will convert to direct stream")
                
                if all_audio_formats:
                    # Sort HLS formats by quality
                    sorted_hls = sorted(all_audio_formats,
                                       key=lambda x: x.get('abr') or 0,
                                       reverse=True)
                    best_hls_format = sorted_hls[0]
                    candidate_url = best_hls_format.get('url')
                    
                    print(f"Converting HLS format: {best_hls_format.get('ext')} - {best_hls_format.get('abr')}kbps")
                    
                    if candidate_url:
                        converted_url = self._convert_hls_to_direct_url(candidate_url, video_id)
                        if converted_url:
                            best_audio_url = converted_url
                            print(f"Successfully converted HLS to direct audio file")
                        else:
                            print("HLS conversion failed - this video may not be playable")
                            # Không fallback về HLS URL nữa vì nó không work
                            best_audio_url = None
            
            # Strategy 3: Fallback to any format with audio
            if not best_audio_url:
                print("Falling back to any format with audio...")
                all_audio_formats = [f for f in formats if f.get('acodec') != 'none']
                if all_audio_formats:
                    # Prefer lower resolution video formats if audio-only not available
                    sorted_all = sorted(all_audio_formats,
                                       key=lambda x: (x.get('height') or 0, x.get('abr') or 0))
                    candidate_url = sorted_all[0].get('url')
                    
                    if candidate_url and self._is_hls_url(candidate_url):
                        print("Fallback: Attempting HLS conversion...")
                        converted_url = self._convert_hls_to_direct_url(candidate_url, video_id)
                        best_audio_url = converted_url if converted_url else candidate_url
                    else:
                        best_audio_url = candidate_url
                else:
                    print("No audio formats found, using original URL")
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
                "id": video_id,
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
    
    def _is_hls_url(self, url: str) -> bool:
        """Check if URL is HLS/m3u8 stream"""
        if not url:
            return False
        
        hls_indicators = [
            'manifest.googlevideo.com',
            'hls_playlist',
            'm3u8',
            'playlist_type',
            'manifest'
        ]
        
        return any(indicator in url.lower() for indicator in hls_indicators)
     
    def _convert_hls_to_direct_url(self, hls_url: str, video_id: str) -> Optional[str]:
        """Convert HLS URL to direct audio stream using FFmpeg"""
        try:
            ffmpeg_path = self._get_ffmpeg_location()
            if not ffmpeg_path:
                print("FFmpeg not found, cannot convert HLS stream")
                return None
            
            # Create temp output file with unique timestamp
            timestamp = int(time.time())
            output_file = self.audio_dir / f"temp_{video_id}_{timestamp}.m4a"
            
            # Ensure audio directory exists
            self.audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Improved FFmpeg command for HLS conversion
            ffmpeg_exe = os.path.join(ffmpeg_path, "ffmpeg.exe")
            command = [
                ffmpeg_exe,
                "-hide_banner",  # Reduce output noise
                "-loglevel", "info",  # Show useful info
                "-user_agent", random.choice(self.user_agents),
                "-headers", f"User-Agent: {random.choice(self.user_agents)}",
                "-headers", "Accept: */*",
                "-headers", "Accept-Language: en-US,en;q=0.9",
                "-i", hls_url,
                "-c:a", "aac",  # Use AAC codec
                "-b:a", "128k",  # Set bitrate
                "-ar", "44100",  # Sample rate
                "-ac", "2",  # Stereo
                "-vn",  # No video
                "-avoid_negative_ts", "make_zero",
                "-fflags", "+genpts",
                "-t", "300",  # Limit to 5 minutes for faster conversion
                "-f", "mp4",  # MP4 container
                "-movflags", "faststart",
                "-y",  # Overwrite
                str(output_file)
            ]
            
            print(f"Converting HLS to direct stream: {video_id}")
            print(f"Output file: {output_file}")
            print(f"FFmpeg command: {' '.join(command[:8])}... [truncated]")
            
            # Run FFmpeg
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minute timeout
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            print(f"FFmpeg return code: {process.returncode}")
            
            # Show only important output
            if process.stderr:
                stderr_lines = process.stderr.split('\n')
                important_lines = [line for line in stderr_lines if any(keyword in line.lower() for keyword in ['error', 'warning', 'duration', 'bitrate', 'speed'])]
                if important_lines:
                    print("FFmpeg output:")
                    for line in important_lines[-5:]:  # Show last 5 important lines
                        print(f"  {line}")
            
            if process.returncode == 0 and output_file.exists() and output_file.stat().st_size > 0:
                # Return local file path as URL
                local_url = f"/audio/{output_file.name}"
                print(f"✓ Successfully converted HLS to: {local_url}")
                print(f"  File size: {output_file.stat().st_size / (1024*1024):.2f} MB")
                return local_url
            else:
                print(f"✗ FFmpeg conversion failed or output file is empty")
                if output_file.exists():
                    print(f"  Output file size: {output_file.stat().st_size} bytes")
                    output_file.unlink()
                return None
                
        except subprocess.TimeoutExpired:
            print("✗ FFmpeg conversion timeout (3 minutes)")
            if output_file.exists():
                output_file.unlink()
            return None
        except Exception as e:
            print(f"✗ Error converting HLS: {e}")
            return None
    
    def _get_ffmpeg_location(self) -> Optional[str]:
        """Find FFmpeg location, always prioritize project ffmpeg/bin first"""
        
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
                }
            
            # Get video metadata
            thumbnails = info.get('thumbnails', [])
            best_thumbnail = None
            if thumbnails:
                sorted_thumbnails = sorted(thumbnails, 
                                          key=lambda x: ((x.get('width') or 0) * (x.get('height') or 0)), 
                                          reverse=True)
                best_thumbnail = sorted_thumbnails[0].get('url') if sorted_thumbnails else None
            
            duration = info.get('duration', 0)
            tags = info.get('tags', [])
            categories = info.get('categories', [])
            keywords = tags + categories
            keywords = [k for k in keywords if k and k.strip()][:10]
            
            # Return local server path (without domain)
            local_audio_path = f"/audio/{actual_file.name}"
            
            result = {
                "success": True,
                "message": "Audio downloaded successfully",
                "video_data": {
                    "id": video_id,
                    "title": title,
                    "artist": uploader,
                    "thumbnail_url": best_thumbnail,
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