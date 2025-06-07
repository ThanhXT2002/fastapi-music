from fastapi import APIRouter
from app.api.routes import auth
from app.api.routes import song
from app.config.database import Base, engine

api_router = APIRouter()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "FastAPI Music API is running"}

@api_router.get("/init-db")
def init_database():
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "Database initialized successfully"}
    except Exception as e:
        return {"error": str(e)}

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(song.router, prefix="/songs", tags=["Songs"])


