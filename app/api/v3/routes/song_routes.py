from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import os
from pathlib import Path
import aiofiles
from typing import AsyncGenerator

from app.config.database import get_db
from app.config.config import settings
from app.api.v3.schemas.song import SongInfoRequest, APIResponse
from app.api.v3.controllers.song_controller import SongController
from app.api.v3.models.song import SongV3, ProcessingStatus

router = APIRouter(prefix="/songs", tags=["Songs V3"])
song_controller = SongController()

@router.post("/info", response_model=APIResponse)
async def get_song_info(
    request: SongInfoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin bài hát từ YouTube URL và bắt đầu quá trình tải về
    """
    return await song_controller.get_song_info(
        request.youtube_url, 
        db, 
        background_tasks
    )

@router.get("/status/{song_id}", response_model=APIResponse)
def get_song_status(
    song_id: str,
    db: Session = Depends(get_db)
):
    """
    Lấy trạng thái xử lý của bài hát
    """
    return song_controller.get_song_status(song_id, db)

@router.get("/download/{song_id}")
async def download_song(
    song_id: str,
    db: Session = Depends(get_db)
):
    """
    Tải file audio với streaming chunks
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
    
    # Streaming function
    async def file_streamer(file_path: Path, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(chunk_size):
                yield chunk
    
    # Return streaming response
    return StreamingResponse(
        file_streamer(file_path),
        media_type='audio/mpeg',
        headers={
            'Content-Disposition': f'attachment; filename="{song.title}.m4a"',
            'Content-Length': str(file_size),
            'Accept-Ranges': 'bytes'
        }
    )

@router.get("/thumbnail/{song_id}")
async def get_thumbnail(
    song_id: str,
    db: Session = Depends(get_db)
):
    """
    Lấy thumbnail đã tải về (optional - vì có thể dùng thumbnail_url gốc)
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
    
    async def file_streamer(file_path: Path) -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(8192):
                yield chunk
    
    return StreamingResponse(
        file_streamer(file_path),
        media_type=media_type
    )
