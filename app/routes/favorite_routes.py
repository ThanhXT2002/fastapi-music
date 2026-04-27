"""Dinh tuyen cac API yeu thich (Favorite).

Module nay ket noi cac endpoint /api/v1/favorites voi
cac phuong thuc trong FavoriteController.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.controllers.favorite_controller import FavoriteController
from app.schemas.song import FavoriteRequest
from app.schemas.base import ApiResponse
from app.config.database import get_db
from app.routes.user import get_current_user_id


router = APIRouter(prefix="/favorites", tags=["Favorites"])
controller = FavoriteController()


@router.get("", response_model=ApiResponse)
def get_user_favorites(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="So luong bai hat"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Lay danh sach bai hat yeu thich cua user hien tai."""
    return controller.get_user_favorites(request, limit, db, user_id)


@router.get("/ids", response_model=ApiResponse)
def get_favorite_ids(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Lay danh sach cac ID bai hat yeu thich de check trang thai UI."""
    return controller.get_favorite_ids(db, user_id)


@router.post("", response_model=ApiResponse)
def add_favorite(
    req: FavoriteRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Them bai hat vao danh sach yeu thich."""
    return controller.add_favorite(req, db, user_id)


@router.delete("/{song_id}", response_model=ApiResponse)
def remove_favorite(
    song_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Xoa bai hat khoi danh sach yeu thich."""
    return controller.remove_favorite(song_id, db, user_id)
