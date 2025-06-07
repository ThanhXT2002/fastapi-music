from fastapi import APIRouter, Depends
from app.api.controllers.song import SongController
from app.api.middleware.auth import get_current_user_optional
from app.api.validators.song import (
   VideoInfoResponse
)

router = APIRouter()

@router.post("/info", response_model=VideoInfoResponse)
async def getInfoVideo(
    url: str,
    controller: SongController = Depends()
):
    """Get video information from YouTube URL without downloading
    
    Returns basic information about a YouTube video including title, artist, 
    thumbnail URL, and duration, without actually downloading the video.
    """
    return controller.get_video_info(url)
