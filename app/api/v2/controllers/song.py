from fastapi import HTTPException, Response, Header
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.orm import Session
import os
import json

from app.api.v2.schemas.song import (
    SearchResponse, DownloadInfo, FileInfo, ProcessRequest, 
    ProcessResponse, DownloadEvent, Song as SongSchema
)
from app.api.v2.helpers import (
    search_music, count_search_results, get_song_by_id,
    calculate_md5, get_file_size, log_download_event, get_audio_path, get_thumbnail_path
)
from app.api.v2.services.youtube_service_v2 import YouTubeServiceV2
from app.config.database import get_db


class SongController:
    youtube_service = YouTubeServiceV2()
    
    @staticmethod
    async def search_songs(q: str, limit: int = 20, offset: int = 0) -> SearchResponse:
        """Search for songs by title, artist, or keywords"""
        db = next(get_db())
        try:
            songs = await search_music(q, limit, offset, db)
            total = await count_search_results(q, db)
            
            return SearchResponse(
                songs=songs,
                total=total
            )
        finally:
            db.close()

    @staticmethod
    async def get_download_info(song_id: str) -> DownloadInfo:
        """Get download information for a song"""
        db = next(get_db())
        try:
            song = await get_song_by_id(song_id, db)
            
            if not song:
                raise HTTPException(status_code=404, detail="Song not found")
            
            if song.is_processing:
                return DownloadInfo(
                    song_id=song_id,
                    ready=False,
                    processing=True
                )
            
            if not song.is_ready:
                return DownloadInfo(
                    song_id=song_id,
                    ready=False,
                    error=song.processing_error or "Song processing failed"
                )
              # Calculate file info
            # Use the actual file path from database or fallback to default path
            audio_path = song.audio_file_path or get_audio_path(song_id)
            file_size = await get_file_size(audio_path)
            chunks_needed = (file_size // 1048576) + (1 if file_size % 1048576 else 0)
            
            return DownloadInfo(
                song_id=song_id,
                ready=True,
                audio_url=f"/api/v2/songs/{song_id}/download",
                thumbnail_url=f"/api/v2/songs/{song_id}/thumbnail",
                file_info=FileInfo(
                    size=file_size,
                    chunks=chunks_needed if file_size > 5 * 1024 * 1024 else 1,
                    checksum=await calculate_md5(audio_path)                )
            )
        finally:
            db.close()

    @staticmethod
    async def download_song(song_id: str) -> FileResponse:
        """Download complete audio file"""
        db = next(get_db())
        try:
            song = await get_song_by_id(song_id, db)
            
            if not song or not song.is_ready:
                raise HTTPException(status_code=404, detail="Song not available")
            
            # Debug: Print the actual path from database
            print(f"Database audio path: {song.audio_file_path}")
            
            # Try multiple possible paths
            possible_paths = [
                song.audio_file_path,
                get_audio_path(song_id),
                f"uploads/audio/{song_id}.m4a",
                f"E:/API/fastapi-music/uploads/audio/{song_id}.m4a"
            ]
            
            # Find existing file
            audio_path = None
            for path in possible_paths:
                if path and os.path.exists(path):
                    audio_path = path
                    print(f"Found audio file at: {audio_path}")
                    break
                else:
                    print(f"Path not found: {path}")
            
            if not audio_path:
                # Try to find any m4a file with video ID in uploads/audio
                import glob
                pattern = "uploads/audio/dQw4w9WgXcQ_*.m4a"
                matches = glob.glob(pattern)
                if matches:
                    audio_path = matches[0]
                    print(f"Found file by pattern: {audio_path}")
                else:
                    raise HTTPException(status_code=404, detail="Audio file not found")
            
            # Log download event
            await log_download_event(song_id, "started", db=db)
            
            return FileResponse(
                path=audio_path,
                media_type="audio/mpeg",
                filename=f"{song.title} - {song.artist}.m4a"
            )
        finally:
            db.close()

    @staticmethod
    async def download_thumbnail(song_id: str) -> FileResponse:
        """Download thumbnail image"""
        db = next(get_db())
        try:
            song = await get_song_by_id(song_id, db)
            
            if not song:
                raise HTTPException(status_code=404, detail="Song not found")
            
            thumbnail_path = get_thumbnail_path(song_id)
            if not os.path.exists(thumbnail_path):
                raise HTTPException(status_code=404, detail="Thumbnail not found")
            
            return FileResponse(
                path=thumbnail_path,
                media_type="image/jpeg"
            )
        finally:
            db.close()

    @staticmethod
    async def download_chunk(song_id: str, chunk_index: int, range_header: Optional[str] = None) -> Response:
        """Download specific chunk of audio file"""
        db = next(get_db())
        try:
            song = await get_song_by_id(song_id, db)
            
            if not song or not song.is_ready:
                raise HTTPException(status_code=404, detail="Song not available")
            
            file_path = get_audio_path(song_id)
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Audio file not found")
            
            file_size = os.path.getsize(file_path)
            chunk_size = 1048576  # 1MB
            
            start = chunk_index * chunk_size
            end = min(start + chunk_size - 1, file_size - 1)
            
            if start >= file_size:
                raise HTTPException(status_code=404, detail="Chunk not found")
            
            # Read chunk data
            with open(file_path, "rb") as f:
                f.seek(start)
                chunk_data = f.read(end - start + 1)
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(len(chunk_data))
            }
            
            return Response(
                content=chunk_data,
                status_code=206,  # Partial Content
                headers=headers,
                media_type="audio/mpeg"            )
        finally:
            db.close()

    @staticmethod
    async def process_song(request: ProcessRequest) -> ProcessResponse:
        """Request song processing from external source"""
        try:
            # Validate YouTube URL
            if not any(domain in request.song_url for domain in ['youtube.com', 'youtu.be']):
                return ProcessResponse(
                    success=False,
                    message="Invalid YouTube URL",
                    status="failed"
                )
            
            # Create song entry and start download
            song_id = await SongController.youtube_service.create_song_from_url(
                request.song_url, 
                request.quality
            )
            
            if not song_id:
                return ProcessResponse(
                    success=False,
                    message="Failed to process song",
                    status="failed"
                )
            
            return ProcessResponse(
                success=True,
                message="Song added to processing queue",
                song_id=song_id,
                status="queued"
            )
            
        except Exception as e:
            return ProcessResponse(
                success=False,
                message=f"Failed to process song: {str(e)}",
                status="failed"
            )

    @staticmethod
    async def track_download(event: DownloadEvent):
        """Track download events for analytics"""
        db = next(get_db())
        try:
            await log_download_event(
                song_id=event.song_id,
                event_type=event.event_type,
                error_message=event.error_message,
                db=db
            )
            
            return {"success": True, "message": "Event logged"}
        finally:
            db.close()
    
    @staticmethod
    async def get_download_progress(song_id: str):
        """Get download progress for a song"""
        return await SongController.youtube_service.get_download_progress(song_id)
    
    @staticmethod
    async def retry_download(song_id: str):
        """Retry failed download"""
        success = await SongController.youtube_service.retry_failed_download(song_id)
        
        if success:
            return {"success": True, "message": "Download retry started"}
        else:
            return {"success": False, "message": "Could not retry download"}
