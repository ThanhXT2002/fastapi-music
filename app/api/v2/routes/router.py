from fastapi import APIRouter
from app.api.v2.routes.song import router as song_router

# Main V2 API Router
api_v2_router = APIRouter()

# Include all V2 route modules
api_v2_router.include_router(song_router, tags=["Songs V2"])

# Health check endpoint for V2
@api_v2_router.get("/health")
async def health_check():
    """Health check endpoint for API V2"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "message": "FastAPI Music API V2 is running"
    }
