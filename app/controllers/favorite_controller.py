"""Controller xu ly nghiep vu Yeu thich (Favorite).

Module nay chua FavoriteController cung cap cac API de them,
xoa, va lay danh sach bai hat yeu thich cua nguoi dung.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.services.favorite_service import FavoriteService
from app.schemas.song import FavoriteRequest
from app.schemas.base import ApiResponse
from app.config.database import get_db
from app.routes.user import get_current_user_id


class FavoriteController:
    """Controller cho cac endpoint Favorite."""

    def __init__(self):
        self.favorite_service = FavoriteService()

    def get_user_favorites(
        self,
        request: Request,
        limit: int = 100,
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user_id)
    ) -> ApiResponse:
        """Lay danh sach bai hat yeu thich cua nguoi dung hien tai."""
        return self.favorite_service.get_user_favorites(
            user_id=user_id,
            db=db,
            limit=limit,
            request=request
        )

    def get_favorite_ids(
        self,
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user_id)
    ) -> ApiResponse:
        """Lay danh sach ID bai hat yeu thich de dong bo UI."""
        return self.favorite_service.get_favorite_ids(
            user_id=user_id,
            db=db
        )

    def add_favorite(
        self,
        req: FavoriteRequest,
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user_id)
    ) -> ApiResponse:
        """Them bai hat vao danh sach yeu thich."""
        return self.favorite_service.add_favorite(
            user_id=user_id,
            song_id=req.song_id,
            db=db
        )

    def remove_favorite(
        self,
        song_id: str,
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user_id)
    ) -> ApiResponse:
        """Xoa bai hat khoi danh sach yeu thich."""
        return self.favorite_service.remove_favorite(
            user_id=user_id,
            song_id=song_id,
            db=db
        )
