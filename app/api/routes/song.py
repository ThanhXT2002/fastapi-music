from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.api.controllers.song import SongController
from app.api.middleware.auth import get_current_user_optional, get_current_user
from app.api.validators.song import (
    SongCreate, SongUpdate, SongResponse,
    YouTubeDownloadRequest, YouTubeDownloadResponse,
    SongSyncRequest, SongSyncResponse
)

router = APIRouter()

@router.get("/", response_model=List[SongResponse])
async def get_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    controller: SongController = Depends(),
    current_user = Depends(get_current_user_optional)
):
    """Get songs - user songs if authenticated, public songs if not"""
    return controller.get_songs(skip, limit, current_user)

@router.get("/search", response_model=List[SongResponse])
async def search_songs(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=50),
    controller: SongController = Depends(),
    current_user = Depends(get_current_user_optional)
):
    """Search songs by title, artist, or album"""
    return controller.search_songs(q, skip, limit, current_user)

@router.get("/favorites", response_model=List[SongResponse])
async def get_favorites(
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Get user's favorite songs (authenticated users only)"""
    return controller.get_favorites(current_user)

@router.get("/recently-played", response_model=List[SongResponse])
async def get_recently_played(
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Get recently played songs (authenticated users only)"""
    return controller.get_recently_played(current_user)

@router.post("/download", response_model=YouTubeDownloadResponse)
async def download_from_youtube(
    request: YouTubeDownloadRequest,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user_optional)
):
    """Download song from YouTube URL"""
    return controller.download_from_youtube(request, current_user)

@router.post("/sync", response_model=SongSyncResponse)
async def sync_songs(
    request: SongSyncRequest,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Sync songs from frontend (authenticated users only)"""
    return controller.sync_songs(request, current_user)

@router.get("/{song_id}", response_model=SongResponse)
async def get_song(
    song_id: str,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user_optional)
):
    """Get single song by ID"""
    return controller.get_song(song_id, current_user)

@router.post("/", response_model=SongResponse)
async def create_song(
    song_data: SongCreate,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Create new song (authenticated users only)"""
    return controller.create_song(song_data, current_user)

@router.put("/{song_id}", response_model=SongResponse)
async def update_song(
    song_id: str,
    song_data: SongUpdate,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Update song (owner only)"""
    return controller.update_song(song_id, song_data, current_user)

@router.delete("/{song_id}")
async def delete_song(
    song_id: str,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Delete song (owner only)"""
    return controller.delete_song(song_id, current_user)

@router.post("/{song_id}/favorite", response_model=SongResponse)
async def toggle_favorite(
    song_id: str,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user)
):
    """Toggle favorite status of a song"""
    return controller.toggle_favorite(song_id, current_user)

@router.post("/{song_id}/play", response_model=SongResponse)
async def play_song(
    song_id: str,
    controller: SongController = Depends(),
    current_user = Depends(get_current_user_optional)
):
    """Play song (increment play count)"""
    return controller.play_song(song_id, current_user)
