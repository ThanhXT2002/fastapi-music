from fastapi import APIRouter
from app.api.routes import auth
from app.api.routes import song

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "FastAPI Music API is running"}

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(song.router, prefix="/songs", tags=["Songs"])
