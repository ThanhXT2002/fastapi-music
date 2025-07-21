from fastapi import APIRouter

from app.routes.song_routes import router as song_router
from app.routes.auth import router as auth_router
from app.routes.ytmusic_routes import router as ytmusic_router

api_router = APIRouter()


api_router.include_router(song_router)
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(ytmusic_router)

@api_router.get("/health")
async def health_check():
    """Health check endpoint for the API"""
    return {
        "success": True,
        "message": "FastAPI Music is running",
        "version": "3.0.0"
    }
