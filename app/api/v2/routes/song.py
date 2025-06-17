from fastapi import APIRouter, Query, Header, Depends
from typing import Optional

from app.api.v2.schemas.song import (
    SearchResponse, DownloadInfo, ProcessRequest, 
    ProcessResponse, DownloadEvent
)
from app.api.v2.controllers.song import SongController

router = APIRouter()

@router.get("/songs/search", response_model=SearchResponse)
async def search_songs(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search for songs by title, artist, or keywords"""
    return await SongController.search_songs(q, limit, offset)


@router.get("/songs/{song_id}/download-info", response_model=DownloadInfo)
async def get_download_info(song_id: str):
    """Get download information for a song"""
    return await SongController.get_download_info(song_id)


@router.get("/songs/{song_id}/download")
async def download_song(song_id: str):
    """Download complete audio file"""
    return await SongController.download_song(song_id)


@router.get("/songs/{song_id}/thumbnail")
async def download_thumbnail(song_id: str):
    """Download thumbnail image"""
    return await SongController.download_thumbnail(song_id)


@router.get("/songs/{song_id}/download/chunk/{chunk_index}")
async def download_chunk(
    song_id: str, 
    chunk_index: int,
    range: Optional[str] = Header(None)
):
    """Download specific chunk of audio file"""
    return await SongController.download_chunk(song_id, chunk_index, range)


@router.post("/songs/process", response_model=ProcessResponse)
async def process_song(request: ProcessRequest):
    """Request song processing from external source"""
    return await SongController.process_song(request)


@router.get("/songs/{song_id}/progress")
async def get_download_progress(song_id: str):
    """Get download progress for a song"""
    return await SongController.get_download_progress(song_id)


@router.post("/songs/{song_id}/retry")
async def retry_download(song_id: str):
    """Retry failed download"""
    return await SongController.retry_download(song_id)


@router.post("/analytics/download")
async def track_download(event: DownloadEvent):
    """Track download events for analytics"""
    return await SongController.track_download(event)


@router.get("/songs/{song_id}/progress")
async def get_download_progress(song_id: str):
    """Get download progress for a song"""
    return await SongController.get_download_progress(song_id)


@router.post("/songs/{song_id}/retry")
async def retry_download(song_id: str):
    """Retry failed download"""
    return await SongController.retry_download(song_id)
