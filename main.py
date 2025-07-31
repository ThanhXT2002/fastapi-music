from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path

from app.routes.router import api_router  
from app.config.config import settings
from app.config.database import Base, engine, create_tables, get_database_info

from app.models.user import User
try:
    from app.models.song import Song
except ImportError:
    print("models not available")


# Create database tables
try:
    create_tables()
    db_info = get_database_info()
    print(f"Database connected successfully")
    print(f"Database type: {db_info['database_type']}")
    if db_info.get('database_file'):
        print(f"Database file: {db_info['database_file']}")
except Exception as e:
    print(f"Database connection failed: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,  # Lấy từ file .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API router
app.include_router(api_router, prefix="/api")

# Mount static files for audio and thumbnails
app.mount("/audio", StaticFiles(directory=settings.AUDIO_DIRECTORY), name="audio")
app.mount("/thumbnails", StaticFiles(directory=settings.THUMBNAIL_DIRECTORY), name="thumbnails")

# Serve test HTML file
@app.get("/test")
async def serve_test():
    """Serve test streaming HTML page"""
    from fastapi.responses import FileResponse
    return FileResponse("test_streaming.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)