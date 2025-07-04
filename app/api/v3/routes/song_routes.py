from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.api.v3.schemas.song import SongInfoRequest, APIResponse
from app.api.v3.controllers.song_controller import SongController

router = APIRouter(prefix="/songs", tags=["Songs V3"])
song_controller = SongController()

@router.post("/info", response_model=APIResponse)
async def get_song_info(
    request_data: SongInfoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin bài hát từ YouTube URL và bắt đầu quá trình tải về
    Body format: {"youtube_url": "https://www.youtube.com/watch?v=..."}
    """
    return await song_controller.get_song_info(
        request_data.youtube_url, 
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
    download: bool = Query(default=False, description="True để download file, False để streaming"),
    db: Session = Depends(get_db)
):
    """
    Stream hoặc download file audio
    - download=false (mặc định): Streaming trực tiếp cho HTML5 audio
    - download=true: Download file về máy
    """
    # Sử dụng controller để lấy thông tin file
    file_data = await song_controller.get_audio_file(song_id, db)
    
    # Chọn Content-Disposition dựa trên parameter
    disposition = "attachment" if download else "inline"
    
    # Return streaming response
    return StreamingResponse(
        song_controller.file_streamer(file_data["file_path"]),
        media_type='audio/mpeg',
        headers={
            'Content-Disposition': f'{disposition}; filename="{file_data["safe_filename"]}"',
            'Content-Length': str(file_data["file_size"]),
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=3600'
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

@router.get("/completed", response_model=APIResponse)
async def get_completed_songs(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Number of songs to return (1-1000, default 100)"),
    key: str = Query(default=None, description="Keyword to search for similar songs (fuzzy matching)"),
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả bài hát đã hoàn thành với URL streaming
    
    Parameters:
    - limit: Số lượng bài hát trả về (1-1000, mặc định 100)
    - key: Từ khóa để tìm kiếm bài hát có keyword gần giống (nếu không truyền thì lấy tất cả)
    """
    return await song_controller.get_completed_songs(db, limit, request, key)
