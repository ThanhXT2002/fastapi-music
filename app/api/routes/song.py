from fastapi import APIRouter, Depends

from app.api.controllers.song import SongController
from app.api.middleware.auth import get_current_user_optional
from app.api.validators.song import (
    YouTubeDownloadRequest, YouTubeDownloadResponse
)

router = APIRouter()

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
