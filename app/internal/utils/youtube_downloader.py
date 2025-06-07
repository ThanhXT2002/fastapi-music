import yt_dlp
import os
import json
import uuid
import random
import time
import asyncio
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from app.config.config import settings
import os
import shutil
import subprocess
from pathlib import Path

class YouTubeDownloader:
    """
    Class chính để download và extract thông tin từ YouTube
    - Xử lý bot detection của YouTube
    - Retry tự động khi gặp lỗi
    - Random delays để giống user thật
    """
    
    def __init__(self):
        """
        Khởi tạo YouTubeDownloader
        - Tạo thư mục lưu audio và thumbnail
        - Chuẩn bị danh sách User-Agents để tránh bot detection
        """
        # Tạo đường dẫn thư mục từ settings
        self.audio_dir = Path(settings.AUDIO_DIRECTORY)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIRECTORY)
        
        # Tạo thư mục nếu chưa tồn tại
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        
        # Danh sách User-Agents để xoay vòng (giả mạo browser khác nhau)
        # Giúp tránh YouTube phát hiện bot
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
    
    def _get_ydl_opts(self, download=False):
        """
        Tạo cấu hình cho yt-dlp với các biện pháp chống bot detection
        
        Args:
            download (bool): True nếu muốn download, False chỉ extract info
            
        Returns:
            dict: Cấu hình yt-dlp
        """
        # Cấu hình cơ bản
        opts = {
            'quiet': True,  # Không hiển thị log verbose
            'no_warnings': True,  # Tắt warnings
            'extract_flat': False,  # Extract đầy đủ thông tin
            'writethumbnail': False,  # Mặc định không tải thumbnail (sẽ override khi download)
            'writeinfojson': False,  # Không ghi file JSON info
            
            # Headers để giả mạo browser thật
            'http_headers': {
                'User-Agent': random.choice(self.user_agents),  # Random User-Agent
                'Accept-Language': 'en-US,en;q=0.9',  # Ngôn ngữ ưu tiên
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',  # Hỗ trợ compression
                'DNT': '1',  # Do Not Track
                'Connection': 'keep-alive',  # Giữ kết nối
                'Upgrade-Insecure-Requests': '1',  # Upgrade HTTP thành HTTPS
            },
            
            # Cấu hình đặc biệt cho YouTube
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],  # Bỏ qua HLS và DASH streams
                    'player_skip': ['configs', 'webpage'],  # Bỏ qua một số bước
                    'player_client': ['android', 'web']  # Thử cả Android và Web client
                }
            },
            
            # Cấu hình timeout và retry
            'socket_timeout': 30,  # Timeout kết nối 30 giây
            'retries': 3,  # Retry 3 lần nếu fail
            'fragment_retries': 3,  # Retry fragments 3 lần
            'sleep_interval': 1,  # Delay tối thiểu giữa các retry
            'max_sleep_interval': 5,  # Delay tối đa giữa các retry
        }
        
        # Nếu là download, thêm cấu hình xử lý audio
        if download:
            opts.update({
                'format': 'bestaudio/best',  # Ưu tiên audio chất lượng cao
                'writethumbnail': True,  # Tải thumbnail khi download
                'writeinfojson': False,  # Vẫn không cần info JSON
                
                # Cấu hình FFmpeg để convert sang MP3
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',  # Sử dụng FFmpeg extract audio
                    'preferredcodec': 'mp3',  # Format MP3
                    'preferredquality': '192',  # Bitrate 192kbps
                }],
                'postprocessor_args': [
                    '-ar', '44100'  # Sample rate 44.1kHz
                ],
                'prefer_ffmpeg': True,  # Ưu tiên dùng FFmpeg
                'keepvideo': False,  # Không giữ file video
                'extractaudio': True,  # Chỉ extract audio
                'audioformat': 'mp3',  # Format đầu ra
                'audioquality': 192,  # Chất lượng audio
            })
        
        return opts
    
    async def extract_info_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Extract thông tin video với retry logic và delay tự động
        
        Args:
            url (str): URL YouTube
            max_retries (int): Số lần retry tối đa
            
        Returns:
            Optional[Dict]: Thông tin video hoặc None nếu fail
        """
        for attempt in range(max_retries):
            try:
                # Thêm delay ngẫu nhiên giữa các lần thử (trừ lần đầu)
                if attempt > 0:
                    delay = random.uniform(2, 5)  # Delay 2-5 giây
                    print(f"Đang chờ {delay:.1f} giây trước khi thử lại...")
                    await asyncio.sleep(delay)
                
                # Lấy cấu hình yt-dlp
                ydl_opts = self._get_ydl_opts(download=False)
                
                # Extract thông tin
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info
                    
            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e).lower()
                
                # Xử lý lỗi bot detection
                if "sign in to confirm" in error_msg or "not a bot" in error_msg:
                    print(f"YouTube phát hiện bot ở lần thử {attempt + 1}")
                    if attempt < max_retries - 1:
                        # Exponential backoff: delay tăng theo cấp số nhân
                        delay = (2 ** attempt) + random.uniform(1, 3)
                        print(f"Đang chờ {delay:.1f} giây trước khi thử lại...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print("Đã thử tối đa số lần. YouTube vẫn chặn bot detection.")
                        return None
                        
                # Xử lý lỗi video không khả dụng
                elif "video unavailable" in error_msg or "private video" in error_msg:
                    print(f"Video không khả dụng hoặc riêng tư: {url}")
                    return None
                    
                # Xử lý các lỗi khác
                else:
                    print(f"Lỗi download ở lần thử {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Chờ 2 giây rồi thử lại
                        continue
                    return None
                    
            except Exception as e:
                print(f"Lỗi không mong muốn ở lần thử {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                return None
        
        return None
    
    def extract_info(self, url: str) -> Optional[Dict]:
        """
        Wrapper đồng bộ cho extract_info_with_retry
        Chuyển async function thành sync để dễ sử dụng
        
        Args:
            url (str): URL YouTube
            
        Returns:
            Optional[Dict]: Thông tin video
        """
        try:
            # Tạo event loop mới để chạy async function
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.extract_info_with_retry(url))
                return result
            finally:
                loop.close()  # Đóng loop khi xong
        except Exception as e:
            print(f"Lỗi trong extract_info: {e}")
            return None
            
    def get_video_details(self, url: str) -> Dict:
        """
        Lấy thông tin cơ bản của video cho frontend (không download)
        
        Args:
            url (str): URL YouTube
            
        Returns:
            Dict: Thông tin video với các field: success, title, artist, thumbnail_url, etc.
        """
        try:
            # Extract thông tin video
            info = self.extract_info(url)
            if not info:
                return {
                    "success": False,
                    "message": "Không thể lấy thông tin video. YouTube có thể đang chặn requests."
                }
              
            # Lấy tiêu đề và người upload
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown Artist')
              
            # Sử dụng tên channel làm artist, giữ nguyên title từ YouTube
            artist = uploader
              
            # Tìm thumbnail chất lượng cao nhất
            thumbnails = info.get('thumbnails', [])
            best_thumbnail = None
            if thumbnails:
                # Sắp xếp theo độ phân giải (width x height) và chọn cao nhất
                sorted_thumbnails = sorted(thumbnails, 
                                          key=lambda x: ((x.get('width') or 0) * (x.get('height') or 0)), 
                                          reverse=True)
                best_thumbnail = sorted_thumbnails[0].get('url') if sorted_thumbnails else None
            
            # Tìm stream audio trực tiếp (không có video)
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            best_audio_url = None
            if audio_formats:
                # Sắp xếp theo bitrate và chọn chất lượng cao nhất
                sorted_formats = sorted(audio_formats,
                                       key=lambda x: x.get('abr') or 0,
                                       reverse=True)
                best_audio_url = sorted_formats[0].get('url') if sorted_formats else None
            
            # Nếu không tìm thấy audio-only format, dùng URL gốc
            if not best_audio_url:
                best_audio_url = url
              
            # Lấy thời lượng video
            duration = info.get('duration', 0)
            
            # Extract keywords từ tags và categories
            tags = info.get('tags', [])
            categories = info.get('categories', [])
            keywords = tags + categories
            # Giới hạn 10 keywords đầu tiên và loại bỏ keywords rỗng
            keywords = [k for k in keywords if k and k.strip()][:10]
            
            # Tạo kết quả trả về
            result = {
                "success": True,
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
                "message": f"Lỗi khi xử lý video: {str(e)}"
            }
    
    def _format_duration(self, seconds: int) -> str:
        """
        Chuyển đổi giây thành format mm:ss hoặc hh:mm:ss
        
        Args:
            seconds (int): Số giây
            
        Returns:
            str: Thời gian đã format
        """
        if not seconds:
            return "00:00"
        
        # Tách giờ, phút, giây
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format theo hh:mm:ss nếu có giờ, ngược lại mm:ss
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def download_audio(self, url: str, filename: Optional[str] = None) -> Tuple[bool, str, Optional[Dict], Optional[str]]:
        """
        Download audio từ YouTube URL với các biện pháp chống bot detection
        
        Args:
            url (str): URL YouTube
            filename (Optional[str]): Tên file tùy chọn, nếu không có sẽ tạo UUID
            
        Returns:
            Tuple[bool, str, Optional[Dict], Optional[str]]: 
                (success, message/path, song_data, thumbnail_path)
        """
        try:
            # Tạo tên file unique nếu không được cung cấp
            if not filename:
                filename = str(uuid.uuid4())
            
            # Tạo đường dẫn output cho audio và thumbnail
            audio_path = self.audio_dir / f"{filename}.%(ext)s"
            thumbnail_path = self.thumbnail_dir / f"{filename}.%(ext)s"
            
            # Tìm FFmpeg (cần thiết để convert audio)
            ffmpeg_location = self._get_ffmpeg_location()
            
            # Lấy cấu hình yt-dlp cho download
            ydl_opts = self._get_ydl_opts(download=True)
            ydl_opts['outtmpl'] = str(audio_path)  # Set output template
            
            # Thêm FFmpeg location nếu tìm thấy
            if ffmpeg_location:
                ydl_opts['ffmpeg_location'] = ffmpeg_location
            
            # Thêm delay ngẫu nhiên trước khi download (giống user thật)
            time.sleep(random.uniform(1, 3))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info trước khi download
                info = ydl.extract_info(url, download=False)
                
                # Thực hiện download
                ydl.download([url])
                
                # Xác định đường dẫn file đã download
                audio_file = self.audio_dir / f"{filename}.mp3"
                info_file = self.audio_dir / f"{filename}.info.json"
                
                # Tìm và di chuyển thumbnail vào thư mục đúng
                thumbnail_file = None
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    potential_thumb = self.audio_dir / f"{filename}.{ext}"
                    if potential_thumb.exists():
                        # Di chuyển thumbnail sang thư mục thumbnail
                        target_thumb = self.thumbnail_dir / f"{filename}.{ext}"
                        potential_thumb.rename(target_thumb)
                        thumbnail_file = target_thumb
                        break
                
                # Chuẩn bị dữ liệu bài hát
                song_data, thumbnail_path = self._extract_song_data(
                    info, 
                    str(audio_file), 
                    str(thumbnail_file) if thumbnail_file else None
                )
                
                return True, str(audio_file), song_data, thumbnail_path
                
        except yt_dlp.utils.DownloadError as e:
            # Xử lý lỗi bot detection
            if "sign in to confirm" in str(e).lower():
                return False, "YouTube phát hiện bot. Vui lòng thử lại sau.", None, None
            return False, f"Download thất bại: {str(e)}", None, None
        except Exception as e:
            return False, f"Download thất bại: {str(e)}", None, None
    
    def _extract_song_data(self, info: Dict, audio_path: str, thumbnail_path: Optional[str] = None) -> Tuple[Dict, Optional[str]]:
        """
        Extract dữ liệu bài hát từ thông tin YouTube
        
        Args:
            info (Dict): Thông tin video từ yt-dlp
            audio_path (str): Đường dẫn file audio
            thumbnail_path (Optional[str]): Đường dẫn thumbnail
            
        Returns:
            Tuple[Dict, Optional[str]]: (song_data, thumbnail_path)
        """
        # Lấy thời lượng bài hát
        duration = info.get('duration', 0)
        
        # Lấy tiêu đề và artist
        title = info.get('title', 'Unknown')
        uploader = info.get('uploader', 'Unknown')
        
        # Thử parse artist và title từ tiêu đề video
        artist = uploader
        if ' - ' in title:
            # Nếu title có format "Artist - Song", tách ra
            parts = title.split(' - ', 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        
        # Extract metadata khác
        description = info.get('description', '')
        upload_date = info.get('upload_date', '')
        view_count = info.get('view_count', 0)
        
        # Format ngày upload
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
        
        # Tạo URL HTTP để serve files
        audio_filename = os.path.basename(audio_path) if audio_path else None
        thumbnail_filename = os.path.basename(thumbnail_path) if thumbnail_path else None
        
        # Tạo URLs đầy đủ để serve files (với domain)
        base_url = settings.BASE_URL.rstrip('/')
        audio_url = f"{base_url}/uploads/audio/{audio_filename}" if audio_filename else None
        thumbnail_url = f"{base_url}/uploads/thumbnails/{thumbnail_filename}" if thumbnail_filename else None
        
        # Tạo dữ liệu bài hát
        song_data = {
            'title': title,
            'artist': artist,
            'album': None,  # YouTube videos thường không có thông tin album
            'duration': duration,
            'source_url': info.get('webpage_url'),  # URL YouTube gốc
            'audio_local_path': audio_path,  # Đường dẫn file audio local
            'thumbnail_local_path': thumbnail_path,  # Đường dẫn thumbnail local
            'keywords': json.dumps(keywords[:10]) if keywords else None,  # Convert thành JSON string
            'is_favorite': False,  # Giá trị mặc định
        }
        
        return song_data, thumbnail_path
    
    def get_playlist_info(self, url: str) -> Optional[Dict]:
        """
        Lấy thông tin playlist
        
        Args:
            url (str): URL playlist YouTube
            
        Returns:
            Optional[Dict]: Thông tin playlist
        """
        ydl_opts = self._get_ydl_opts(download=False)
        ydl_opts['extract_flat'] = True  # Chỉ lấy list videos, không extract chi tiết
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            print(f"Lỗi khi lấy thông tin playlist: {e}")
            return None
    
    def download_playlist(self, url: str, max_downloads: int = 10) -> List[Tuple[bool, str, Optional[Dict], Optional[str]]]:
        """
        Download nhiều videos từ playlist
        
        Args:
            url (str): URL playlist
            max_downloads (int): Số lượng video tối đa để download
            
        Returns:
            List[Tuple]: Danh sách kết quả download
        """
        # Lấy thông tin playlist
        playlist_info = self.get_playlist_info(url)
        if not playlist_info or 'entries' not in playlist_info:
            return []
        
        results = []
        entries = playlist_info['entries'][:max_downloads]  # Giới hạn số lượng
        
        for i, entry in enumerate(entries):
            if entry and entry.get('url'):
                # Thêm delay giữa các downloads để tránh bị ban
                if i > 0:
                    time.sleep(random.uniform(3, 6))  # Delay 3-6 giây
                
                # Tạo URL video
                video_url = entry.get('url')
                if not video_url.startswith('http'):
                    video_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                
                # Download video
                result = self.download_audio(video_url)
                results.append(result)
        
        return results
    
    def _get_ffmpeg_location(self) -> Optional[str]:
        """
        Tìm vị trí FFmpeg, ưu tiên ffmpeg trong project trước
        
        Returns:
            Optional[str]: Đường dẫn thư mục chứa FFmpeg
        """
        # Luôn ưu tiên ffmpeg trong project root trước
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        project_ffmpeg = project_root / "ffmpeg" / "bin"
        ffmpeg_exe = project_ffmpeg / "ffmpeg.exe"
        
        if ffmpeg_exe.exists():
            print(f"Sử dụng project ffmpeg: {project_ffmpeg}")
            return str(project_ffmpeg)
        
        # Fallback: tìm ffmpeg trong PATH
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            print(f"Sử dụng system ffmpeg: {os.path.dirname(ffmpeg_path)}")
            return os.path.dirname(ffmpeg_path)
        
        # Cuối cùng: thử các vị trí phổ biến khác
        possible_paths = [
            os.path.join(os.getcwd(), "ffmpeg", "bin"),
            f"C:\\ffmpeg\\bin",
            "C:\\Program Files\\ffmpeg\\bin",
            "C:\\Program Files (x86)\\ffmpeg\\bin"
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "ffmpeg.exe")):
                print(f"Sử dụng fallback ffmpeg: {path}")
                return path
        
        print("Không tìm thấy FFmpeg ở bất kỳ vị trí nào")
        return None