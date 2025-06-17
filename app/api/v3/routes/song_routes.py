from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.api.v3.schemas.song import SongInfoRequest, APIResponse
from app.api.v3.controllers.song_controller import SongController

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
    # Sử dụng controller để lấy thông tin file
    file_data = await song_controller.get_audio_file(song_id, db)
    
    # Return streaming response
    return StreamingResponse(
        song_controller.file_streamer(file_data["file_path"]),
        media_type='audio/mpeg',
        headers={
            'Content-Disposition': f'attachment; filename="{file_data["safe_filename"]}"',
            'Content-Length': str(file_data["file_size"]),
            'Accept-Ranges': 'bytes'
        }
    )

@router.get("/thumbnail/{song_id}")
async def get_thumbnail(
    song_id: str,
    db: Session = Depends(get_db)
):
    """
    Lấy thumbnail đã tải về
    """
    # Sử dụng controller để lấy thông tin thumbnail
    thumbnail_data = await song_controller.get_thumbnail_file(song_id, db)
    
    return StreamingResponse(
        song_controller.file_streamer(thumbnail_data["file_path"]),
        media_type=thumbnail_data["media_type"],
        headers={
            'Content-Disposition': f'inline; filename="{thumbnail_data["safe_filename"]}"'
        }
    )
