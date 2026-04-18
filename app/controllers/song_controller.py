"""Controller xu ly toan bo nghiep vu lien quan den bai hat.

Module nay chua:
- SongController: nhan dien bai hat (ACRCloud), lay thong tin YouTube,
  download/streaming audio, proxy thumbnail, tim kiem fuzzy.

Lien quan:
- Route:   app/routes/song_routes.py
- Service: app/services/youtube_service.py
- Model:   app/models/song.py
- Schema:  app/schemas/song.py
"""

# ── Standard library imports ──────────────────────────────
import asyncio
import base64
import hashlib
import hmac
import mimetypes
import os
import random
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

# ── Third-party imports ───────────────────────────────────
import aiofiles
import httpx
import yt_dlp
from fastapi import HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from unidecode import unidecode

# ── Internal imports ──────────────────────────────────────
from app.models.song import Song, ProcessingStatus
from app.schemas.base import ApiResponse
from app.schemas.song import (
    SongInfoResponse, StatusResponse, APIResponse,
    CompletedSongResponse, CompletedSongsListResponse,
    CompletedSongsQueryParams,
)
from app.services.youtube_service import YouTubeService
from app.config.config import settings


class SongController:
    """Controller xu ly cac thao tac voi bai hat.

    Chiu trach nhiem:
        - Nhan dien bai hat tu file audio qua ACRCloud.
        - Lay thong tin va bat dau download tu YouTube.
        - Streaming/download file audio da xu ly.
        - Proxy thumbnail tu YouTube hoac tu disk.
        - Tim kiem fuzzy bai hat da hoan thanh.
        - Long-poll download cho co che proxy.
    """

    def __init__(self):
        self.youtube_service = YouTubeService()
        
        
    def identify_song_by_file(self, file_bytes: bytes) -> APIResponse:
        """Nhan dien bai hat tu file audio qua ACRCloud HTTP API.

        Gui file audio len ACRCloud de fingerprint matching,
        tra ve metadata bai hat (title, artist, album...).

        Args:
            file_bytes: Noi dung file audio dang bytes.

        Returns:
            APIResponse chua thong tin bai hat hoac thong bao loi.
        """
        host = os.getenv("ACR_CLOUD_HOST", getattr(settings, "ACR_CLOUD_HOST", ""))
        access_key = os.getenv("ACR_CLOUD_ACCESS_KEY", getattr(settings, "ACR_CLOUD_ACCESS_KEY", ""))
        access_secret = os.getenv("ACR_CLOUD_ACCESS_SECRET", getattr(settings, "ACR_CLOUD_ACCESS_SECRET", ""))
        requrl = f"https://{host}/v1/identify"
        http_method = "POST"
        http_uri = "/v1/identify"
        data_type = "audio"
        signature_version = "1"
        timestamp = str(int(time.time()))
        string_to_sign = http_method + "\n" + http_uri + "\n" + access_key + "\n" + data_type + "\n" + signature_version + "\n" + timestamp
        sign = base64.b64encode(hmac.new(access_secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha1).digest()).decode('utf-8')

        if not host or not access_key or not access_secret:
            return ApiResponse.fail(message="Missing ACRCloud credentials")
        if not file_bytes or len(file_bytes) < 128:
            return ApiResponse.fail(message="Audio file is empty or too small")

        file_name = 'sample.mp4'
        file_type, _ = mimetypes.guess_type(file_name)
        if not file_type:
            file_type = 'application/octet-stream'
        files = [
            ('sample', (file_name, file_bytes, file_type))
        ]
        data = {
            'access_key': access_key,
            'sample_bytes': len(file_bytes),
            'timestamp': timestamp,
            'signature': sign,
            'data_type': data_type,
            'signature_version': signature_version
        }
        try:
            r = httpx.post(requrl, files=files, data=data, timeout=15)
            r.encoding = "utf-8"
            result = r.json() if r.status_code == 200 else None
            if result and result.get("status", {}).get("msg") == "Success":
                music = result.get("metadata", {}).get("music", [{}])[0]
                song_info = {
                    "title": music.get("title"),
                    "artist": ", ".join([a.get("name") for a in music.get("artists", [])]),
                    "album": music.get("album", {}).get("name"),
                    "release_date": music.get("release_date"),
                    "score": music.get("score"),
                    "external_ids": music.get("external_ids", {}),
                    "external_metadata": music.get("external_metadata", {}),
                }
                return ApiResponse.ok(data=song_info, message="Song identified successfully")
            else:
                error_msg = result.get("status", {}).get("msg") if result else r.text
                return APIResponse(success=False, message=f"Could not identify song: {error_msg}", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"Error: {str(e)}", data=None)
    
    def get_domain_url(self, request: Request) -> str:
        """Xac dinh domain URL tu request headers.

        Uu tien doc proxy headers (ngrok, cloudflare, nginx),
        roi fallback ve request.base_url, cuoi cung la settings.

        Args:
            request: FastAPI Request object.

        Returns:
            Base URL dang "https://domain.com" (khong trailing slash).
        """
        try:
            forwarded_proto = request.headers.get('x-forwarded-proto')
            forwarded_host = request.headers.get('x-forwarded-host')

            if forwarded_proto and forwarded_host:
                return f"{forwarded_proto}://{forwarded_host}"

            host = request.headers.get('host')
            if host:
                if (
                    'https' in str(request.url)
                    or request.headers.get('x-forwarded-proto') == 'https'
                ):
                    return f"https://{host}"
                else:
                    return f"http://{host}"

            base_url = str(request.base_url).rstrip('/')
            return base_url
        except Exception:
            return settings.BASE_URL
    
    def sanitize_filename(self, filename: str) -> str:
        """Lam sach ten file de dung trong Content-Disposition header.

        Loai bo emoji, ky tu non-ASCII, va cac ky tu dac biet
        khong hop le trong ten file.

        Args:
            filename: Ten file goc (co the chua Unicode).

        Returns:
            Ten file da lam sach, chi chua ky tu ASCII hop le.
        """
        filename = unicodedata.normalize('NFKD', filename)
        filename = re.sub(r'[^\x00-\x7F]+', '', filename)
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        filename = filename.strip('. ')
        if not filename:
            filename = "audio_file"
        return filename
    
    def normalize_vietnamese_text(self, text: str) -> str:
        """Chuan hoa van ban tieng Viet bang bo dau qua unidecode.

        Vi du:
            - "hung" -> "hung"
            - "khong loi" -> "khong loi"
            - "nhac" -> "nhac"

        Args:
            text: Chuoi can chuan hoa.

        Returns:
            Chuoi da bo dau, lowercase, da trim khoang trang.
        """
        if not text:
            return ""
        text = text.lower()
        normalized = unidecode(text)
        return re.sub(r'\s+', ' ', normalized).strip()
    
    async def get_song_info(
        self,
        youtube_url: str,
        db: Session,
        background_tasks: BackgroundTasks,
    ) -> APIResponse:
        """Lay thong tin bai hat va bat dau download trong background.

        Flow xu ly:
            1. Trich xuat video ID tu URL.
            2. Kiem tra ban ghi da ton tai trong DB.
            3. Neu song da COMPLETED -> tra ve ngay.
            4. Neu chua -> lay metadata tu YouTube, tao ban ghi,
               khoi dong background task download.

        Args:
            youtube_url: URL YouTube hop le.
            db: Database session.
            background_tasks: FastAPI background task runner.

        Returns:
            APIResponse chua metadata bai hat.

        Raises:
            HTTPException 400: URL khong hop le hoac loi YouTube.
        """
        try:
            video_id = self.youtube_service.extract_video_id(youtube_url)
            
            existing_song = None
            if video_id:
                existing_song = db.query(Song).filter(Song.id == video_id).first()
            

            if existing_song and existing_song.status == ProcessingStatus.COMPLETED:
                response_data = SongInfoResponse(
                    id=existing_song.id,
                    title=existing_song.title,
                    artist=existing_song.artist,
                    thumbnail_url=existing_song.thumbnail_url,
                    duration=existing_song.duration,
                    duration_formatted=existing_song.duration_formatted,
                    keywords=existing_song.keywords.split(',') if existing_song.keywords else [],
                    original_url=existing_song.original_url,
                    created_at=existing_song.created_at
                )
                
                return ApiResponse.ok(data=response_data.model_dump(), message="Song already available")
            
            video_info = await self.youtube_service.get_video_info(
                youtube_url, 
                quick_check=(existing_song is not None)
            )
            
            if not existing_song:
                existing_song = db.query(Song).filter(Song.id == video_info['id']).first()
            
            if existing_song:
                response_data = SongInfoResponse(
                    id=existing_song.id,
                    title=existing_song.title,
                    artist=existing_song.artist,
                    thumbnail_url=existing_song.thumbnail_url,
                    duration=existing_song.duration,
                    duration_formatted=existing_song.duration_formatted,
                    keywords=existing_song.keywords.split(',') if existing_song.keywords else [],
                    original_url=existing_song.original_url,
                    created_at=existing_song.created_at
                )
                
                # Chua hoan thanh -> restart download
                if existing_song.status != ProcessingStatus.COMPLETED:
                    background_tasks.add_task(
                        self.youtube_service.download_audio_and_thumbnail,
                        existing_song.id,
                        youtube_url,
                        db
                    )
            else:
                new_song = Song(
                    id=video_info['id'],
                    title=video_info['title'],
                    artist=video_info['artist'],
                    thumbnail_url=video_info['thumbnail_url'],
                    duration=video_info['duration'],
                    duration_formatted=video_info['duration_formatted'],
                    keywords=','.join(video_info['keywords']),
                    original_url=video_info['original_url'],
                    status=ProcessingStatus.PENDING
                )
                
                db.add(new_song)
                db.commit()
                db.refresh(new_song)
                
                response_data = SongInfoResponse(
                    id=new_song.id,
                    title=new_song.title,
                    artist=new_song.artist,
                    thumbnail_url=new_song.thumbnail_url,
                    duration=new_song.duration,
                    duration_formatted=new_song.duration_formatted,
                    keywords=new_song.keywords.split(',') if new_song.keywords else [],
                    original_url=new_song.original_url,
                    created_at=new_song.created_at
                )
                

                background_tasks.add_task(
                    self.youtube_service.download_audio_and_thumbnail,
                    new_song.id,
                    youtube_url,
                    db
                )
            
            return ApiResponse.ok(data=response_data.model_dump(), message="get info video success")
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get video info: {str(e)}")
    
    def get_song_status(self, song_id: str, db: Session) -> APIResponse:
        """Lay trang thai xu ly hien tai cua bai hat.

        Args:
            song_id: YouTube video ID.
            db: Database session.

        Returns:
            APIResponse chua trang thai va progress.

        Raises:
            HTTPException 404: Bai hat khong ton tai.
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        progress = None
        if song.status == ProcessingStatus.PENDING:
            progress = 0.0
        elif song.status == ProcessingStatus.PROCESSING:
            # Uoc luong 50% vi khong co progress chi tiet tu yt-dlp
            progress = 0.5
        elif song.status == ProcessingStatus.COMPLETED:
            progress = 1.0
        elif song.status == ProcessingStatus.FAILED:
            progress = 0.0
        
        status_data = StatusResponse(
            id=song.id,
            status=song.status,
            progress=progress,
            error_message=song.error_message,
            audio_filename=song.audio_filename,
            thumbnail_filename=song.thumbnail_filename,
            updated_at=song.updated_at
        )
        
        return ApiResponse.ok(data=status_data.model_dump(), message="Status retrieved successfully")
        
    async def get_audio_file(self, song_id: str, db: Session):
        """Lay duong dan file audio da download de phuc vu streaming.

        Thu nhieu pattern tim file: ten chinh xac tu DB,
        them .m4a extension, glob theo song_id.

        Args:
            song_id: YouTube video ID.
            db: Database session.

        Returns:
            Dict chua file_path, file_size, safe_filename.

        Raises:
            HTTPException 400: Bai hat chua hoan thanh.
            HTTPException 404: Bai hat hoac file khong ton tai.
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        if song.status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Song is not ready for download. Status: {song.status.value}"
            )
        
        if not song.audio_filename:
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        audio_dir = Path(settings.AUDIO_DIRECTORY)
        possible_paths = []

        possible_paths.append(audio_dir / song.audio_filename)

        if not song.audio_filename.endswith('.m4a'):
            possible_paths.append(audio_dir / f"{song.audio_filename}.m4a")

        for audio_file in audio_dir.glob(f"{song_id}_*.m4a"):
            if audio_file.is_file():
                possible_paths.append(audio_file)

        if song.audio_filename.endswith('.m4a'):
            possible_paths.append(
                audio_dir / song.audio_filename.replace('.m4a', '')
            )

        file_path = None
        for path in possible_paths:
            if path.exists() and path.is_file():
                file_path = path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Audio file not found on server")
        
        file_size = file_path.stat().st_size
        safe_filename = self.sanitize_filename(song.title)
        
        return {
            "file_path": file_path,
            "file_size": file_size,
            "safe_filename": f"{safe_filename}.m4a"
        }
    
    async def get_thumbnail_file(self, song_id: str, db: Session):
        """Lay file thumbnail tu disk hoac proxy tu YouTube.

        Uu tien file da download tren server. Neu chua co
        thi proxy truc tiep tu thumbnail_url goc.

        Args:
            song_id: YouTube video ID.
            db: Database session.

        Returns:
            Dict chua file_path/content, media_type, safe_filename.

        Raises:
            HTTPException 404: Khong co thumbnail.
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        if song.thumbnail_filename:
            file_path = (
                Path(settings.THUMBNAIL_DIRECTORY)
                / song.thumbnail_filename
            )

            if file_path.exists():
                media_type = "image/jpeg"
                if file_path.suffix.lower() in ['.png']:
                    media_type = "image/png"
                elif file_path.suffix.lower() in ['.webp']:
                    media_type = "image/webp"
                
                safe_filename = self.sanitize_filename(song.title)
                file_ext = file_path.suffix
                
                return {
                    "file_path": file_path,
                    "media_type": media_type,
                    "safe_filename": f"{safe_filename}{file_ext}",
                    "proxy": False
                }
        
        # Chua co file tren disk -> proxy tu YouTube URL goc
        if song.thumbnail_url and song.thumbnail_url.startswith('http'):
            try:
                user_agent = random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                ])
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                }
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        song.thumbnail_url, headers=headers, timeout=15
                    )
                    response.raise_for_status()

                content_type = response.headers.get('Content-Type', 'image/jpeg')

                return {
                    "proxy": True,
                    "content": response.content,
                    "media_type": content_type,
                    "safe_filename": f"{song_id}.webp"
                }
            except Exception as e:
                print(f"Error proxying thumbnail: {e}")
        
        raise HTTPException(status_code=404, detail="Thumbnail not available")
    
    async def file_streamer(
        self, file_path: Path, chunk_size: int = 262144
    ) -> AsyncGenerator[bytes, None]:
        """Stream file theo tung chunk (async generator).

        Args:
            file_path: Duong dan file can stream.
            chunk_size: Kich thuoc moi chunk (bytes). Mac dinh 256KB.

        Yields:
            Tung chunk bytes cua file.
        """
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(chunk_size):
                yield chunk
    
    async def get_completed_songs(
        self,
        db: Session,
        limit: int = 100,
        request: Request = None,
        search_key: str | None = None,
    ) -> APIResponse:
        """Lay danh sach bai hat da hoan thanh kem URL streaming.

        Ho tro tim kiem fuzzy theo title, artist, keywords voi
        co che: DB ILIKE truoc -> fallback sang in-memory fuzzy.

        Args:
            db: Database session.
            limit: So luong bai hat toi da. Mac dinh 100.
            request: HTTP request (de tao base URL cho streaming).
            search_key: Tu khoa tim kiem (nullable, fuzzy matching).

        Returns:
            APIResponse chua danh sach bai hat da hoan thanh.

        Raises:
            HTTPException 500: Loi truy van database.
        """
        try:
            if not isinstance(limit, int) or limit < 1:
                limit = 100
            elif limit > 1000:
                limit = 1000

            query = db.query(Song).filter(
                Song.status == ProcessingStatus.COMPLETED,
                Song.audio_filename.isnot(None)
            )
            
            if search_key:
                search_key_lower = search_key.lower().strip()
                search_key_normalized = unidecode(search_key_lower)

                # DB ILIKE truoc — nhanh hon in-memory voi dataset lon
                db_filtered = query.filter(
                    or_(
                        Song.keywords.ilike(f'%{search_key_lower}%'),
                        Song.title.ilike(f'%{search_key_lower}%'),
                        Song.artist.ilike(f'%{search_key_lower}%'),
                        Song.keywords.ilike(f'%{search_key_normalized}%'),
                        Song.title.ilike(f'%{search_key_normalized}%'),
                        Song.artist.ilike(f'%{search_key_normalized}%'),
                    )
                ).order_by(Song.created_at.desc()).all()
                
                # Fallback: DB khong match -> in-memory fuzzy
                if len(db_filtered) == 0:
                    all_songs = query.order_by(
                        Song.created_at.desc()
                    ).all()
                    filtered_songs = self._filter_songs_by_fuzzy_keywords(
                        all_songs, search_key
                    )
                    completed_songs = filtered_songs[:limit]
                elif len(db_filtered) <= limit * 2:
                    filtered_songs = self._filter_songs_by_fuzzy_keywords(
                        db_filtered, search_key
                    )
                    completed_songs = filtered_songs[:limit]
                else:
                    all_songs = query.order_by(
                        Song.created_at.desc()
                    ).all()
                    filtered_songs = self._filter_songs_by_fuzzy_keywords(
                        all_songs, search_key
                    )
                    completed_songs = filtered_songs[:limit]
            else:
                completed_songs = query.order_by(
                    Song.created_at.desc()
                ).limit(limit).all()
            
            songs_data = []
            base_url = (
                self.get_domain_url(request)
                if request else settings.BASE_URL
            )

            for song in completed_songs:
                audio_url = f"{base_url}/api/songs/download/{song.id}"
                thumbnail_url = f"{base_url}/api/songs/thumbnail/{song.id}"

                keywords = [k.strip() for k in song.keywords.split(',') if k.strip()] if song.keywords else []
                
                song_data = CompletedSongResponse(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                    duration=song.duration,
                    duration_formatted=song.duration_formatted,
                    thumbnail_url=thumbnail_url,
                    audio_url=audio_url,
                    keywords=keywords
                )
                songs_data.append(song_data)
            
            response_data = CompletedSongsListResponse(
                songs=songs_data,
                total=len(songs_data)
            )
            
            search_info = f" matching '{search_key}'" if search_key else ""
            return APIResponse(
                success=True,
                message=f"Retrieved {len(songs_data)} completed songs{search_info} (limit: {limit})",
                data=response_data.model_dump()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get completed songs: {str(e)}")
    
    def _filter_songs_by_fuzzy_keywords(self, songs, search_key: str):
        """Tim kiem fuzzy in-memory voi unidecode normalization.

        Kiem tra keywords -> title -> artist theo do uu tien
        giam dan. Toi uu cho <100ms voi ~5000 bai hat.

        Args:
            songs: Danh sach Song objects can filter.
            search_key: Tu khoa tim kiem.

        Returns:
            Danh sach Song da sap xep theo relevance score.
        """
        if not search_key:
            return songs
            
        search_lower = search_key.lower().strip()
        search_normalized = unidecode(search_lower)
        search_words = search_normalized.split()
        
        matched_songs = []

        for song in songs:
            score = 0

            if song.keywords:
                keywords_norm = unidecode(song.keywords.lower())
                keyword_score = self._quick_field_score(
                    search_lower, search_normalized, search_words,
                    song.keywords.lower(), keywords_norm, multiplier=3
                )
                score += keyword_score

            if score < 80 and song.title:
                title_norm = unidecode(song.title.lower())
                title_score = self._quick_field_score(
                    search_lower, search_normalized, search_words,
                    song.title.lower(), title_norm, multiplier=2
                )
                score += title_score

            if score < 40 and song.artist:
                artist_norm = unidecode(song.artist.lower())
                artist_score = self._quick_field_score(
                    search_lower, search_normalized, search_words,
                    song.artist.lower(), artist_norm, multiplier=1
                )
                score += artist_score

            if score > 0:
                matched_songs.append((song, score))

        matched_songs.sort(key=lambda x: x[1], reverse=True)
        
        return [song for song, _ in matched_songs]
    
    def _quick_field_score(
        self, search_orig: str, search_norm: str,
        search_words: list[str], field_orig: str,
        field_norm: str, multiplier: int = 1,
    ) -> int:
        """Tinh diem relevance giua search term va mot truong.

        So sanh theo thu tu uu tien giam dan:
        exact match > substring > reverse substring > word match > prefix/suffix.

        Args:
            search_orig: Tu khoa goc (lowercase).
            search_norm: Tu khoa da unidecode.
            search_words: Danh sach tung tu da unidecode.
            field_orig: Gia tri truong goc (lowercase).
            field_norm: Gia tri truong da unidecode.
            multiplier: He so nhan diem (keywords=3, title=2, artist=1).

        Returns:
            Diem relevance (cao = phu hop hon).
        """
        if search_orig == field_orig or search_norm == field_norm:
            return 50 * multiplier

        if search_orig in field_orig or search_norm in field_norm:
            return 35 * multiplier

        if field_orig in search_orig or field_norm in search_norm:
            return 25 * multiplier

        if any(
            word in field_norm
            for word in search_words if len(word) >= 2
        ):
            return 15 * multiplier

        for word in search_words:
            if len(word) >= 3:
                for field_word in field_norm.split():
                    if len(field_word) >= 3:
                        if (
                            field_word.startswith(word)
                            and len(word) >= len(field_word) * 0.6
                        ):
                            return 20 * multiplier
                        if (
                            field_word.endswith(word)
                            and len(word) >= len(field_word) * 0.6
                        ):
                            return 18 * multiplier
        
        return 0


    async def proxy_download_audio(
        self, song_id: str, request: Request, db: Session
    ):
        """Long-poll download: cho background task xong roi stream ve FE.

        Flow xu ly:
            1. Neu song da COMPLETED va file ton tai -> serve tu disk.
            2. Neu chua -> poll DB moi 2s cho background task hoan thanh.
            3. Timeout sau 3 phut (180s).

        Loi ich: FE chi can 1 HTTP request duy nhat, nhan blob audio
        hoan chinh (.m4a da qua FFmpeg), luu vao IndexedDB.

        Khong tu goi yt-dlp vi se gay dual download -> YouTube chan bot.

        Args:
            song_id: YouTube video ID.
            request: HTTP request.
            db: Database session.

        Returns:
            StreamingResponse audio.

        Raises:
            HTTPException 404: Bai hat khong ton tai.
            HTTPException 502: Download that bai.
            HTTPException 504: Timeout sau 3 phut.
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        

        if song.status == ProcessingStatus.COMPLETED and song.audio_filename:
            audio_dir = Path(settings.AUDIO_DIRECTORY)
            file_path = audio_dir / song.audio_filename
            
            if file_path.exists() and file_path.stat().st_size > 1024:
                return await self.stream_file_with_range(request, str(file_path))
        
        MAX_WAIT_SECONDS = 180
        POLL_INTERVAL = 2
        waited = 0
        
        while waited < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_INTERVAL)
            waited += POLL_INTERVAL
            

            db.expire(song)
            db.refresh(song)
            
            if song.status == ProcessingStatus.COMPLETED and song.audio_filename:
                audio_dir = Path(settings.AUDIO_DIRECTORY)
                file_path = audio_dir / song.audio_filename
                
                if file_path.exists() and file_path.stat().st_size > 1024:
                    return await self.stream_file_with_range(request, str(file_path))
            
            elif song.status == ProcessingStatus.FAILED:
                raise HTTPException(
                    status_code=502,
                    detail=f"Download thất bại: {song.error_message or 'Lỗi không xác định'}"
                )
        

        raise HTTPException(
            status_code=504,
            detail="Timeout: background task chưa hoàn thành sau 3 phút"
        )


    async def stream_file_with_range(
        self, request: Request, file_path: str,
        chunk_size: int = 262144,
    ):
        """Stream file voi ho tro HTTP Range request.

        Ho tro partial content (206) cho HTML5 audio seeking.
        Neu khong co Range header, tra ve toan bo file (200).

        Args:
            request: HTTP request (doc Range header).
            file_path: Duong dan file tren disk.
            chunk_size: Kich thuoc moi chunk. Mac dinh 256KB.

        Returns:
            StreamingResponse voi Content-Range header.

        Raises:
            HTTPException 416: Range khong hop le.
        """
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('range')
        start = 0
        end = file_size - 1

        if range_header:

            bytes_range = range_header.replace("bytes=", "").split("-")
            if bytes_range[0]:
                start = int(bytes_range[0])
            if len(bytes_range) > 1 and bytes_range[1]:
                end = int(bytes_range[1])
            if start > end or end >= file_size:
                raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

        async def file_iterator():
            with open(file_path, "rb") as f:
                f.seek(start)
                bytes_to_read = end - start + 1
                while bytes_to_read > 0:
                    chunk = f.read(min(chunk_size, bytes_to_read))
                    if not chunk:
                        break
                    yield chunk
                    bytes_to_read -= len(chunk)

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(end - start + 1),
            "Cache-Control": "public, max-age=3600"
        }
        status_code = 206 if range_header else 200
        return StreamingResponse(file_iterator(), status_code=status_code, headers=headers, media_type="audio/mpeg")