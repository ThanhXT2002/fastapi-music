from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.schemas.playlist import PlaylistCreate, PlaylistResponse, PlaylistTrackAdd
from app.services.playlist_service import PlaylistService
# Assuming get_current_user_id is available in auth (or mock for now like favorite_routes)
from app.routes.favorite_routes import get_current_user_id

router = APIRouter(prefix="/playlists", tags=["Playlists"])

def get_playlist_service(db: Session = Depends(get_db)) -> PlaylistService:
    return PlaylistService(db)

@router.get("", response_model=List[PlaylistResponse])
def get_playlists(
    user_id: str = Depends(get_current_user_id),
    service: PlaylistService = Depends(get_playlist_service)
):
    """Lấy danh sách playlist của người dùng hiện tại"""
    return service.get_user_playlists(user_id)

@router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(
    data: PlaylistCreate,
    user_id: str = Depends(get_current_user_id),
    service: PlaylistService = Depends(get_playlist_service)
):
    """Tạo playlist mới"""
    return service.create_playlist(user_id, data)

@router.post("/{playlist_id}/tracks", status_code=status.HTTP_201_CREATED)
def add_track_to_playlist(
    playlist_id: str,
    data: PlaylistTrackAdd,
    user_id: str = Depends(get_current_user_id),
    service: PlaylistService = Depends(get_playlist_service)
):
    """Thêm bài hát vào playlist"""
    service.add_track_to_playlist(user_id, playlist_id, data.trackId)
    return {"message": "Thêm thành công"}

@router.delete("/{playlist_id}/tracks/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    user_id: str = Depends(get_current_user_id),
    service: PlaylistService = Depends(get_playlist_service)
):
    """Xoá bài hát khỏi playlist"""
    service.remove_track_from_playlist(user_id, playlist_id, track_id)
