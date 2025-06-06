from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.api.controllers.song import SongController
from app.internal.service.song_service import SongService
from app.api.middleware.auth import get_current_user_optional
from app.api.validators.song import (
    SongBase, SongResponse, YouTubeDownloadRequest, YouTubeDownloadResponse
)

router = APIRouter()

def get_song_service(db: Session = Depends(get_db)) -> SongService:
    return SongService(db)

@router.post("/download", response_model=YouTubeDownloadResponse)
async def download_from_youtube(
    url: str,  # Chỉ cần truyền URL string trực tiếp
    controller: SongController = Depends(),
    current_user = Depends(get_current_user_optional)
):
    """Download song from YouTube URL"""
    # Tạo request object với giá trị mặc định
    request = YouTubeDownloadRequest(
        url=url,
        download_audio=True,  # Mặc định luôn download audio
        quality='best'        # Mặc định luôn dùng chất lượng tốt nhất
    )
    return controller.download_from_youtube(request, current_user)

@router.get("/", response_model=List[SongResponse])
async def get_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SongService = Depends(get_song_service)
):
    """Get all songs with pagination"""
    return service.get_all_songs(skip=skip, limit=limit)

@router.get("/user/{user_id}", response_model=List[SongResponse])
async def get_user_songs(
    user_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SongService = Depends(get_song_service)
):
    """Get songs of a specific user"""
    return service.get_user_songs(user_id, skip=skip, limit=limit)

@router.get("/{song_id}", response_model=SongResponse)
async def get_song(
    song_id: str = Path(...),
    service: SongService = Depends(get_song_service)
):
    """Get song by ID"""
    return service.get_song(song_id)

@router.post("/", response_model=SongResponse)
async def create_song(
    song_data: SongBase,
    service: SongService = Depends(get_song_service),
    current_user = Depends(get_current_user_optional)
):
    """Create a new song"""
    user_id = current_user.id if current_user else None
    return service.create_song(song_data, user_id)

@router.put("/{song_id}", response_model=SongResponse)
async def update_song(
    song_id: str = Path(...),
    song_data: dict = ...,
    service: SongService = Depends(get_song_service)
):
    """Update song"""
    return service.update_song(song_id, song_data)

@router.delete("/{song_id}")
async def delete_song(
    song_id: str = Path(...),
    service: SongService = Depends(get_song_service)
):
    """Delete song"""
    return service.delete_song(song_id)

@router.post("/{song_id}/users/{user_id}", response_model=SongResponse)
async def add_user_to_song(
    song_id: str = Path(...),
    user_id: int = Path(..., gt=0),
    service: SongService = Depends(get_song_service)
):
    """Add user to song"""
    return service.add_user_to_song(song_id, user_id)

@router.delete("/{song_id}/users/{user_id}", response_model=SongResponse)
async def remove_user_from_song(
    song_id: str = Path(...),
    user_id: int = Path(..., gt=0),
    service: SongService = Depends(get_song_service)
):
    """Remove user from song"""
    return service.remove_user_from_song(song_id, user_id)

@router.patch("/{song_id}/favorite", response_model=SongResponse)
async def toggle_favorite(
    song_id: str = Path(...),
    service: SongService = Depends(get_song_service)
):
    """Toggle favorite status of a song"""
    return service.toggle_favorite(song_id)
