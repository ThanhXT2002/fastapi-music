from fastapi import APIRouter
from app.api.v3.routes.song_routes import router as song_router

api_v3_router = APIRouter()

# Include all V3 routes
api_v3_router.include_router(song_router)

@api_v3_router.get("/health")
async def health_check():
    """Health check endpoint for V3"""
    return {
        "success": True,
        "message": "FastAPI Music V3 is running",
        "version": "3.0.0"
    }
