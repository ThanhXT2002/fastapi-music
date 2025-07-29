import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, BackgroundTasks, Request
from typing import Optional, AsyncGenerator
import os
from pathlib import Path
import aiofiles
import re
import unicodedata
from unidecode import unidecode

from fastapi.responses import StreamingResponse
import os

import base64
import hashlib
import hmac
import time
import requests
import  mimetypes

from app.models.song import Song, ProcessingStatus
from app.schemas.song import (
    SongInfoResponse, StatusResponse, APIResponse, CompletedSongResponse, CompletedSongsListResponse, CompletedSongsQueryParams
)
from app.services.youtube_service import YouTubeService
from app.config.config import settings

class SongController:

    def __init__(self):
        self.youtube_service = YouTubeService()
        
        
    def identify_song_by_file(self, file_bytes: bytes) -> APIResponse:
        """
        Identify song by file using direct HTTP API integration with ACRCloud.
        """
        
        # Rebase lại hoàn toàn theo tài liệu mẫu ACRCloud
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
        # Validate
        if not host or not access_key or not access_secret:
            return APIResponse(success=False, message="Missing ACRCloud credentials", data=None)
        if not file_bytes or len(file_bytes) < 128:
            return APIResponse(success=False, message="Audio file is empty or too small", data=None)
        # Đặt tên file mặc định, đoán content-type
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
            r = requests.post(requrl, files=files, data=data, timeout=15)
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
                return APIResponse(success=True, message="Song identified successfully", data=song_info)
            else:
                error_msg = result.get("status", {}).get("msg") if result else r.text
                return APIResponse(success=False, message=f"Could not identify song: {error_msg}", data=result)
        except Exception as e:
            return APIResponse(success=False, message=f"Error: {str(e)}", data=None)
    
    def get_domain_url(self, request: Request) -> str:
        """Get domain URL automatically for production or development"""
        try:
            # Check for proxy headers (ngrok, cloudflare, nginx)
            forwarded_proto = request.headers.get('x-forwarded-proto')
            forwarded_host = request.headers.get('x-forwarded-host')
            
            if forwarded_proto and forwarded_host:
                return f"{forwarded_proto}://{forwarded_host}"
            
            # Check for standard proxy headers
            host = request.headers.get('host')
            if host:
                # Check if HTTPS
                if 'https' in str(request.url) or request.headers.get('x-forwarded-proto') == 'https':
                    return f"https://{host}"
                else:
                    return f"http://{host}"
            
            # Fallback to request base URL
            base_url = str(request.base_url).rstrip('/')
            return base_url
        except:
            # Last resort fallback
            return settings.BASE_URL
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to be used in Content-Disposition header:
        - Remove emojis and non-ASCII characters
        - Replace with ASCII approximations when possible
        - Remove/replace special characters
        """
        # NFKD normalization to separate characters from combining marks
        filename = unicodedata.normalize('NFKD', filename)
        # Remove remaining non-ASCII characters
        filename = re.sub(r'[^\x00-\x7F]+', '', filename)
        # Replace problematic characters with underscores
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
        # Remove leading/trailing whitespace and dots
        filename = filename.strip('. ')
        # Ensure we have a valid filename
        if not filename:
            filename = "audio_file"
        return filename
    
    def normalize_vietnamese_text(self, text: str) -> str:
        """
        Normalize Vietnamese text using unidecode for perfect diacritics removal:
        - "hưng" → "hung"
        - "không lời" → "khong loi"  
        - "nhạc" → "nhac"
        """
        if not text:
            return ""
        
        # Convert to lowercase first
        text = text.lower()
        
        # Use unidecode for perfect Vietnamese → ASCII conversion
        normalized = unidecode(text)
        
        # Remove extra spaces and return
        return re.sub(r'\s+', ' ', normalized).strip()
    
    async def get_song_info(
        self, 
        youtube_url: str, 
        db: Session, 
        background_tasks: BackgroundTasks
    ) -> APIResponse:
        """
        Lấy thông tin bài hát và bắt đầu quá trình tải về
        """
        try:
            # First, try to extract video ID quickly without full video info
            video_id = self.youtube_service.extract_video_id(youtube_url)
            
            # Quick check if song already exists using video ID
            existing_song = None
            if video_id:
                existing_song = db.query(Song).filter(Song.id == video_id).first()
            
            # If song exists and is completed, return immediately
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
                
                return APIResponse(
                    success=True,
                    message="Song already available",
                    data=response_data.dict()
                )
            
            # If not found or not completed, get full video info
            # Use quick_check=True if this is for an existing song check
            video_info = await self.youtube_service.get_video_info(
                youtube_url, 
                quick_check=(existing_song is not None)
            )
            
            # Check again with the extracted video info ID (in case URL format was different)
            if not existing_song:
                existing_song = db.query(Song).filter(Song.id == video_info['id']).first()
            
            if existing_song:
                # Return existing song info
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
                
                # If not completed, restart download process
                if existing_song.status != ProcessingStatus.COMPLETED:
                    background_tasks.add_task(
                        self.youtube_service.download_audio_and_thumbnail,
                        existing_song.id,
                        youtube_url,
                        db
                    )
            else:
                # Create new song record
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
                
                # Start background download
                background_tasks.add_task(
                    self.youtube_service.download_audio_and_thumbnail,
                    new_song.id,
                    youtube_url,
                    db
                )
            
            return APIResponse(
                success=True,
                message="get info video success",
                data=response_data.dict()
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get video info: {str(e)}")
    
    def get_song_status(self, song_id: str, db: Session) -> APIResponse:
        """
        Lấy trạng thái xử lý của bài hát
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Calculate progress
        progress = None
        if song.status == ProcessingStatus.PENDING:
            progress = 0.0
        elif song.status == ProcessingStatus.PROCESSING:
            progress = 0.5  # Giả sử 50% khi đang xử lý
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
        
        return APIResponse(
            success=True,
            message="Status retrieved successfully",
            data=status_data.dict()
        )
        
    async def get_audio_file(self, song_id: str, db: Session):
        """
        Lấy file audio để phục vụ download
        """
        # Check if song exists and is completed
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
        
        # Try different file path patterns
        audio_dir = Path(settings.AUDIO_DIRECTORY)
        possible_paths = []
        
        # 1. Exact filename from database
        possible_paths.append(audio_dir / song.audio_filename)
        
        # 2. Add .m4a extension if not present
        if not song.audio_filename.endswith('.m4a'):
            possible_paths.append(audio_dir / f"{song.audio_filename}.m4a")
        
        # 3. Try pattern matching for files starting with song_id
        for audio_file in audio_dir.glob(f"{song_id}_*.m4a"):
            if audio_file.is_file():
                possible_paths.append(audio_file)
        
        # 4. Try without extension if current has extension
        if song.audio_filename.endswith('.m4a'):
            possible_paths.append(audio_dir / song.audio_filename.replace('.m4a', ''))
        
        # Find the first existing file
        file_path = None
        for path in possible_paths:
            if path.exists() and path.is_file():
                file_path = path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Audio file not found on server")
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Sanitize the title for the Content-Disposition header
        safe_filename = self.sanitize_filename(song.title)
        
        return {
            "file_path": file_path,
            "file_size": file_size,
            "safe_filename": f"{safe_filename}.m4a"
        }
    
    async def get_thumbnail_file(self, song_id: str, db: Session):
        """
        Lấy file thumbnail để phục vụ hiển thị
        """
        song = db.query(Song).filter(Song.id == song_id).first()
        
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        if not song.thumbnail_filename:
            raise HTTPException(status_code=404, detail="Thumbnail not available")
        
        file_path = Path(settings.THUMBNAIL_DIRECTORY) / song.thumbnail_filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail file not found")
        
        # Determine media type
        media_type = "image/jpeg"
        if file_path.suffix.lower() in ['.png']:
            media_type = "image/png"
        elif file_path.suffix.lower() in ['.webp']:
            media_type = "image/webp"
        
        # Sanitize the title for the Content-Disposition header
        safe_filename = self.sanitize_filename(song.title)
        file_ext = file_path.suffix
        
        return {
            "file_path": file_path,
            "media_type": media_type,
            "safe_filename": f"{safe_filename}{file_ext}"
        }
    
    async def file_streamer(self, file_path: Path, chunk_size: int = 262144) -> AsyncGenerator[bytes, None]:
        """Helper method to stream files"""
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(chunk_size):
                yield chunk
    
    async def get_completed_songs(self, db: Session, limit: int = 100, request: Request = None, search_key: str = None) -> APIResponse:
        """
        Lấy tất cả bài hát đã hoàn thành với URL streaming
        OPTIMIZED: Tối ưu tốc độ cho database lớn
        """
        try:
            # Validate limit
            if not isinstance(limit, int) or limit < 1:
                limit = 100
            elif limit > 1000:
                limit = 1000
            
            # Base query với index optimization
            query = db.query(Song).filter(
                Song.status == ProcessingStatus.COMPLETED,
                Song.audio_filename.isnot(None)
            )
            
            if search_key:
                # Tối ưu: Thử database search trước nếu có thể
                search_key_lower = search_key.lower().strip()
                search_key_normalized = unidecode(search_key_lower)  # Add normalized version
                
                # Quick database filter trước khi loop - search cả original và normalized
                db_filtered = query.filter(
                    or_(
                        Song.keywords.ilike(f'%{search_key_lower}%'),
                        Song.title.ilike(f'%{search_key_lower}%'),
                        Song.artist.ilike(f'%{search_key_lower}%'),
                        # THÊM: search với normalized text
                        Song.keywords.ilike(f'%{search_key_normalized}%'),
                        Song.title.ilike(f'%{search_key_normalized}%'),
                        Song.artist.ilike(f'%{search_key_normalized}%')
                    )
                ).order_by(Song.created_at.desc()).all()
                
                # DEBUG: Nếu database filter không có kết quả, bypass nó
                if len(db_filtered) == 0:
                    # Fallback: Lấy tất cả songs và filter bằng algorithm
                    all_songs = query.order_by(Song.created_at.desc()).all()
                    filtered_songs = self._filter_songs_by_fuzzy_keywords(all_songs, search_key)
                    completed_songs = filtered_songs[:limit]
                elif len(db_filtered) <= limit * 2:
                    # Apply scoring và limit
                    filtered_songs = self._filter_songs_by_fuzzy_keywords(db_filtered, search_key)
                    completed_songs = filtered_songs[:limit]
                else:
                    # Nếu quá nhiều, lấy tất cả rồi filter
                    all_songs = query.order_by(Song.created_at.desc()).all()
                    filtered_songs = self._filter_songs_by_fuzzy_keywords(all_songs, search_key)
                    completed_songs = filtered_songs[:limit]
            else:
                # Không có search key - query trực tiếp với limit
                completed_songs = query.order_by(Song.created_at.desc()).limit(limit).all()
            
            # Build response nhanh nhất có thể
            songs_data = []
            base_url = self.get_domain_url(request) if request else settings.BASE_URL
            
            for song in completed_songs:
                # Pre-compute URLs
                audio_url = f"{base_url}/api/songs/download/{song.id}"
                thumbnail_url = f"{base_url}/api/songs/thumbnail/{song.id}"
                
                # Quick keyword parsing
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
                data=response_data.dict()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get completed songs: {str(e)}")
    
    def _filter_songs_by_fuzzy_keywords(self, songs, search_key: str):
        """
        ULTRA OPTIMIZED: Fast search với unidecode + simplified algorithm
        Target: <100ms cho 5000 bài hát
        """
        if not search_key:
            return songs
            
        # Pre-normalize search key một lần
        search_lower = search_key.lower().strip()
        search_normalized = unidecode(search_lower)
        search_words = search_normalized.split()
        
        # DEBUG: Print để kiểm tra
        print(f"🔍 Search: '{search_key}' → '{search_lower}' → '{search_normalized}'")
        print(f"📊 Total songs to check: {len(songs)}")
        
        matched_songs = []
        
        for song in songs:
            score = 0
            
            # 1. Quick Keywords check (highest priority)
            if song.keywords:
                keywords_norm = unidecode(song.keywords.lower())
                keyword_score = self._quick_field_score(search_lower, search_normalized, search_words, 
                                               song.keywords.lower(), keywords_norm, multiplier=3)
                score += keyword_score
                
                # DEBUG: Log nếu có match trong keywords
                if keyword_score > 0:
                    print(f"🎯 KEYWORD MATCH: '{song.title}' - Keywords: '{song.keywords}' → Normalized: '{keywords_norm}' - Score: {keyword_score}")
            
            # 2. Title check (nếu chưa đủ điểm)
            if score < 80 and song.title:
                title_norm = unidecode(song.title.lower())
                title_score = self._quick_field_score(search_lower, search_normalized, search_words,
                                               song.title.lower(), title_norm, multiplier=2)
                score += title_score
                
                # DEBUG: Log nếu có match trong title
                if title_score > 0:
                    print(f"📝 TITLE MATCH: '{song.title}' → Normalized: '{title_norm}' - Score: {title_score}")
            
            # 3. Artist check (chỉ khi cần thiết)
            if score < 40 and song.artist:
                artist_norm = unidecode(song.artist.lower())
                artist_score = self._quick_field_score(search_lower, search_normalized, search_words,
                                               song.artist.lower(), artist_norm, multiplier=1)
                score += artist_score
                
                # DEBUG: Log nếu có match trong artist
                if artist_score > 0:
                    print(f"👤 ARTIST MATCH: '{song.artist}' → Normalized: '{artist_norm}' - Score: {artist_score}")
            
            # Add nếu có score
            if score > 0:
                matched_songs.append((song, score))
                print(f"✅ TOTAL MATCH: '{song.title}' - Total Score: {score}")
        
        # Quick sort và return
        matched_songs.sort(key=lambda x: x[1], reverse=True)
        print(f"🏆 Final matches: {len(matched_songs)}")
        
        return [song for song, _ in matched_songs]
    
    def _quick_field_score(self, search_orig, search_norm, search_words, field_orig, field_norm, multiplier=1):
        """
        Simplified scoring function - tối ưu tốc độ
        """
        # 1. Exact match (original hoặc normalized)
        if search_orig == field_orig or search_norm == field_norm:
            return 50 * multiplier
        
        # 2. Substring (original hoặc normalized)
        if search_orig in field_orig or search_norm in field_norm:
            return 35 * multiplier
            
        # 3. Reverse substring
        if field_orig in search_orig or field_norm in search_norm:
            return 25 * multiplier
        
        # 4. Word matching (chỉ với normalized)
        if any(word in field_norm for word in search_words if len(word) >= 2):
            return 15 * multiplier
            
        # 5. Prefix/suffix matching (simplified)
        for word in search_words:
            if len(word) >= 3:
                for field_word in field_norm.split():
                    if len(field_word) >= 3:
                        # Prefix: "tik" in "tiktok"
                        if field_word.startswith(word) and len(word) >= len(field_word) * 0.6:
                            return 20 * multiplier
                        # Suffix: "tok" in "tiktok"  
                        if field_word.endswith(word) and len(word) >= len(field_word) * 0.6:
                            return 18 * multiplier
        
        return 0


    async def stream_file_with_range(self, request: Request, file_path: str, chunk_size: int = 262144):
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('range')
        start = 0
        end = file_size - 1

        if range_header:
            # Parse header: "bytes=START-END"
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