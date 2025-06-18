import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, BackgroundTasks
from typing import Optional, AsyncGenerator
import os
from pathlib import Path
import aiofiles
import re
import unicodedata

from app.api.v3.models.song import SongV3, ProcessingStatus
from app.api.v3.schemas.song import (
    SongInfoResponse, StatusResponse, APIResponse
)
from app.api.v3.services.youtube_service import YouTubeService
from app.config.config import settings

class SongController:
    def __init__(self):
        self.youtube_service = YouTubeService()
    
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
            # Extract video info
            video_info = await self.youtube_service.get_video_info(youtube_url)
            
            # Check if song already exists
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
        
        # Get file path - handle both with and without extension
        file_path = Path(settings.AUDIO_DIRECTORY) / song.audio_filename
        
        # If file doesn't exist, try with .m4a extension
        if not file_path.exists() and not song.audio_filename.endswith('.m4a'):
            file_path = Path(settings.AUDIO_DIRECTORY) / f"{song.audio_filename}.m4a"
        
        # If still doesn't exist, try without extension
        if not file_path.exists() and song.audio_filename.endswith('.m4a'):
            file_path = Path(settings.AUDIO_DIRECTORY) / song.audio_filename.replace('.m4a', '')
        
        if not file_path.exists():
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
