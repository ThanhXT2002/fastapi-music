import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks, Request
from typing import Optional, AsyncGenerator
import os
from pathlib import Path
import aiofiles
import re
import unicodedata

from app.api.v3.models.song import SongV3, ProcessingStatus
from app.api.v3.schemas.song import (
    SongInfoResponse, StatusResponse, APIResponse, CompletedSongResponse, CompletedSongsListResponse, CompletedSongsQueryParams
)
from app.api.v3.services.youtube_service import YouTubeService
from app.config.config import settings

class SongController:
    def __init__(self):
        self.youtube_service = YouTubeService()
    
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
                existing_song = db.query(SongV3).filter(SongV3.id == video_id).first()
            
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
                existing_song = db.query(SongV3).filter(SongV3.id == video_info['id']).first()
            
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
                new_song = SongV3(
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
        song = db.query(SongV3).filter(SongV3.id == song_id).first()
        
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
        song = db.query(SongV3).filter(SongV3.id == song_id).first()
        
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
        song = db.query(SongV3).filter(SongV3.id == song_id).first()
        
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
    
    async def file_streamer(self, file_path: Path, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """Helper method to stream files"""
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(chunk_size):
                yield chunk
    
    async def get_completed_songs(self, db: Session, limit: int = 100, request: Request = None) -> APIResponse:
        """
        Lấy tất cả bài hát đã hoàn thành với URL streaming
        """
        try:
            # Validate limit
            if not isinstance(limit, int) or limit < 1:
                limit = 100
            elif limit > 1000:
                limit = 1000
            
            # Query all completed songs with limit
            completed_songs = db.query(SongV3).filter(
                SongV3.status == ProcessingStatus.COMPLETED,
                SongV3.audio_filename.isnot(None)
            ).order_by(SongV3.created_at.desc()).limit(limit).all()
            
            songs_data = []
            for song in completed_songs:
                # Tự động detect domain từ request
                if request:
                    base_url = self.get_domain_url(request)
                else:
                    base_url = settings.BASE_URL
                
                # Tạo streaming URLs với domain đúng
                audio_url = f"{base_url}/api/v3/songs/download/{song.id}"
                thumbnail_url = f"{base_url}/api/v3/songs/thumbnail/{song.id}"
                
                # Parse keywords
                keywords = []
                if song.keywords:
                    keywords = [k.strip() for k in song.keywords.split(',') if k.strip()]
                
                song_data = CompletedSongResponse(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                    duration=song.duration,
                    duration_formatted=song.duration_formatted,
                    thumbnail_url=thumbnail_url,  # Server streaming URL
                    audio_url=audio_url,
                    keywords=keywords
                )
                songs_data.append(song_data)
            
            response_data = CompletedSongsListResponse(
                songs=songs_data,
                total=len(songs_data)
            )
            
            return APIResponse(
                success=True,
                message=f"Retrieved {len(songs_data)} completed songs (limit: {limit})",
                data=response_data.dict()
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get completed songs: {str(e)}")
