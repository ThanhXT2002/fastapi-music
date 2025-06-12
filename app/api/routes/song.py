from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.api.controllers.song import SongController
from app.api.middleware.auth import get_current_user_optional
from app.api.validators.youtube import (
    YouTubeDownloadRequest,
    YouTubeDownloadResponse,
    RecentDownloadsResponse
)
from app.internal.model.user import User
from typing import Optional

router = APIRouter()



@router.post("/download", response_model=YouTubeDownloadResponse)
async def download_youtube_audio(
    request_data: YouTubeDownloadRequest,
    request: Request,
    db: Session = Depends(get_db),
    controller: SongController = Depends(),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Download YouTube audio với workflow mới:
    - Kiểm tra cache trong SQLite trước
    - Nếu có cache thì trả về response luôn  
    - Nếu không có thì download audio m4a về server
    - Lưu vào database và trả về response với full domain URL
    """
    user_id = current_user.id if current_user else None
    return controller.download_youtube_audio(
        url=request_data.url,
        request=request,
        db=db,
        user_id=user_id
    )

@router.get("/recent-downloads", response_model=RecentDownloadsResponse)
async def get_recent_downloads(
    limit: int = 50,
    db: Session = Depends(get_db),
    controller: SongController = Depends()
):
    """Lấy danh sách các video đã download gần đây từ cache"""
    return controller.get_recent_downloads(db, limit)
