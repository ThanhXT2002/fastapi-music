"""
Xử lý download và lưu trữ audio/thumbnail từ YouTube.

Module này chứa:
- Service download audio từ YouTube bằng yt-dlp.
- Chuyển đổi định dạng audio sang .m4a bằng ffmpeg.
- Download và lưu trữ thumbnail lên server.
- Cập nhật trạng thái xử lý vào database.

Liên quan:
- Model:  song.py (Song, ProcessingStatus)
- Config: config.py (settings.AUDIO_DIRECTORY, settings.THUMBNAIL_DIRECTORY)
"""

# ── Standard library imports ──────────────────────────────
import asyncio
import json
import os
import random
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# ── Third-party imports ───────────────────────────────────
import aiofiles
import requests
import yt_dlp
from sqlalchemy.orm import Session

# ── Internal imports ──────────────────────────────────────
from app.config.config import settings
from app.models.song import ProcessingStatus, Song


class YouTubeService:
    """Xử lý download audio và thumbnail từ YouTube.

    Chịu trách nhiệm:
        - Trích xuất metadata video (title, artist, duration, thumbnail).
        - Download audio và convert sang .m4a bằng ffmpeg.
        - Download thumbnail và lưu lên server.
        - Cập nhật trạng thái xử lý (PROCESSING/COMPLETED/FAILED) vào DB.

    Sử dụng pool User-Agent ngẫu nhiên và delay giữa các request
    để giảm nguy cơ bị YouTube rate-limit hoặc detect bot.
    """

    def __init__(self) -> None:
        self.audio_dir = Path(settings.AUDIO_DIRECTORY)
        self.thumbnail_dir = Path(settings.THUMBNAIL_DIRECTORY)

        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

        # Pool User-Agent giả lập trình duyệt để tránh bị YouTube detect bot
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

    # ── Utility methods ───────────────────────────────────

    def extract_video_id(self, url: str) -> Optional[str]:
        """Trích xuất YouTube video ID từ URL.

        Hỗ trợ nhiều định dạng URL:
            - youtube.com/watch?v=...
            - youtu.be/...
            - youtube.com/embed/...

        Args:
            url: URL YouTube cần phân tích.

        Returns:
            Video ID dạng chuỗi, hoặc None nếu không khớp pattern nào.
        """
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
        """Chuyển đổi thời lượng từ giây sang chuỗi MM:SS hoặc HH:MM:SS.

        Args:
            duration_seconds: Thời lượng tính bằng giây.

        Returns:
            Chuỗi thời lượng đã format (VD: "03:45" hoặc "01:23:45").
        """
        if not duration_seconds:
            return "00:00"

        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    # ── Video info extraction ─────────────────────────────

    async def get_video_info(
        self, url: str, quick_check: bool = False
    ) -> Dict[str, Any]:
        """Lấy metadata video từ YouTube mà không download.

        Trích xuất các thông tin: title, artist, thumbnail URL,
        duration, keywords. Chạy trong thread pool để không block
        event loop của FastAPI.

        Args:
            url: URL YouTube cần lấy thông tin.
            quick_check: Nếu True, giảm timeout và delay cho việc
                kiểm tra nhanh (VD: validate URL trước khi download).

        Returns:
            Dict chứa metadata video với các key:
                id, title, artist, thumbnail_url, duration,
                duration_formatted, keywords, original_url.

        Raises:
            yt_dlp.DownloadError: Khi URL không hợp lệ hoặc video
                không khả dụng.
        """
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
            # Delay ngẫu nhiên trước mỗi request để tránh rate limiting
            time.sleep(random.uniform(*delay_range))
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _extract_info)

        video_id = self.extract_video_id(url)
        if not video_id:
            video_id = info.get('id', str(uuid.uuid4()))

        # Ưu tiên thumbnail chất lượng cao nhất (sắp xếp theo diện tích pixel)
        thumbnail_url = info.get('thumbnail')
        if not thumbnail_url and 'thumbnails' in info:
            thumbnails = info['thumbnails']
            sorted_thumbnails = sorted(
                thumbnails,
                key=lambda x: ((x.get('width') or 0) * (x.get('height') or 0)),
                reverse=True
            )
            if sorted_thumbnails:
                thumbnail_url = sorted_thumbnails[0].get('url')

        # Giới hạn 5 tags để tránh lưu quá nhiều dữ liệu không cần thiết
        keywords = []
        tags = info.get('tags', [])
        categories = info.get('categories', [])
        if tags:
            keywords.extend(tags[:5])
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

    # ── Thumbnail download ────────────────────────────────

    async def download_thumbnail_to_server(
        self, thumbnail_url: str, video_id: str
    ) -> Optional[str]:
        """Download thumbnail từ URL và lưu vào thư mục server.

        Tên file được tạo theo format: {video_id}_{timestamp}.{ext}
        để đảm bảo không trùng lặp khi cùng video được download lại.

        Args:
            thumbnail_url: URL ảnh thumbnail cần download.
            video_id: YouTube video ID, dùng làm prefix tên file.

        Returns:
            Tên file thumbnail đã lưu (VD: "abc123_1713300000.jpg"),
            hoặc None nếu download thất bại hoặc URL rỗng.
        """
        try:
            if not thumbnail_url:
                return None

            timestamp = int(time.time())

            # Xác định extension từ URL, mặc định .jpg nếu không rõ
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

                response = requests.get(
                    thumbnail_url, headers=headers, timeout=30
                )
                response.raise_for_status()

                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)

                # Kiểm tra file tồn tại và có dung lượng hợp lệ
                return thumbnail_path.exists() and thumbnail_path.stat().st_size > 0

            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _download_thumbnail)

            if success:
                return filename
            return None

        except Exception as e:
            print(f"[ERROR] Download thumbnail that bai: {e}")
            return None

    # ── Audio download & processing ───────────────────────

    async def download_audio_and_thumbnail(
        self, song_id: str, url: str, db: Session
    ) -> bool:
        """Download audio và thumbnail trong background, cập nhật DB.

        Flow xử lý:
            1. Cập nhật trạng thái bài hát sang PROCESSING.
            2. Download audio raw bằng yt-dlp (chạy trong thread pool).
            3. Convert sang .m4a bằng ffmpeg subprocess.
            4. Nếu ffmpeg fail, fallback rename file raw thành .m4a.
            5. Download thumbnail.
            6. Cập nhật DB: audio_filename, thumbnail_filename,
               status = COMPLETED.
            7. Nếu có lỗi: status = FAILED + ghi error_message.

        Args:
            song_id: ID bài hát trong database.
            url: URL YouTube cần download.
            db: SQLAlchemy Session để cập nhật trạng thái.

        Returns:
            True nếu download và xử lý thành công, False nếu thất bại.
        """
        try:
            song = db.query(Song).filter(Song.id == song_id).first()
            if not song:
                return False

            song.status = ProcessingStatus.PROCESSING
            db.commit()

            timestamp = int(time.time())

            def _download_audio():
                # Không dùng FFmpegExtractAudio postprocessor vì dễ fail
                # Thay vào đó convert thủ công bằng ffmpeg subprocess
                output_path = self.audio_dir / f"{song_id}_{timestamp}"

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': str(output_path),
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
                }

                # Delay truoc khi download de tranh rate limiting
                time.sleep(random.uniform(1, 3))

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Tim file raw da download (yt-dlp tu them extension)
                raw_file = None
                for file in self.audio_dir.glob(f"{song_id}_{timestamp}*"):
                    # Chi chap nhan file > 1KB de loai file loi/rong
                    if file.is_file() and file.stat().st_size > 1024:
                        raw_file = file
                        break

                if not raw_file:
                    return None

                # Convert sang .m4a bang ffmpeg (copy codec, khong re-encode)
                final_file = self.audio_dir / f"{song_id}_{timestamp}.m4a"

                try:
                    import subprocess
                    result = subprocess.run(
                        ['ffmpeg', '-i', str(raw_file),
                         '-c', 'copy', '-y', str(final_file)],
                        capture_output=True, timeout=120
                    )

                    if (result.returncode == 0
                            and final_file.exists()
                            and final_file.stat().st_size > 1024):
                        # Convert thanh cong — xoa raw file neu khac final file
                        if raw_file != final_file and raw_file.exists():
                            raw_file.unlink()
                        return final_file.name
                    else:
                        # Convert fail — rename raw file thanh .m4a
                        # Browser van phat duoc AAC raw voi extension .m4a
                        if raw_file.suffix.lower() != '.m4a':
                            renamed = raw_file.with_suffix('.m4a')
                            if renamed.exists():
                                renamed.unlink()
                            raw_file.rename(renamed)
                            return renamed.name
                        return raw_file.name

                except Exception as e:
                    print(f"[ERROR] FFmpeg convert that bai: {e}")
                    # Fallback: dung raw file voi extension .m4a
                    if raw_file and raw_file.exists():
                        if raw_file.suffix.lower() != '.m4a':
                            renamed = raw_file.with_suffix('.m4a')
                            if renamed.exists():
                                renamed.unlink()
                            raw_file.rename(renamed)
                            return renamed.name
                        return raw_file.name

                return None

            loop = asyncio.get_event_loop()
            downloaded_audio_filename = await loop.run_in_executor(
                None, _download_audio
            )

            if not downloaded_audio_filename:
                raise Exception("Audio download that bai")

            thumbnail_filename = await self.download_thumbnail_to_server(
                song.thumbnail_url, song_id
            )

            # Cap nhat ket qua vao database
            song.audio_filename = downloaded_audio_filename
            song.thumbnail_filename = thumbnail_filename
            song.status = ProcessingStatus.COMPLETED
            song.completed_at = datetime.utcnow()
            db.commit()

            return True

        except Exception as e:
            if song:
                song.status = ProcessingStatus.FAILED
                song.error_message = str(e)
                db.commit()
            return False
