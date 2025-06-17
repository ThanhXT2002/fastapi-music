from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
from app.api.routes.router import api_router
from app.api.v3.routes.router import api_v3_router  # Import V3 router
from app.config.config import settings
from app.config.database import Base, engine, create_tables, get_database_info

# Import models to ensure they are registered with SQLAlchemy
from app.internal.model.user import User
from app.internal.model.song import Song
from app.internal.model.youtube_cache import YouTubeCache

# Import V3 models
try:
    from app.api.v3.models.song import SongV3
except ImportError:
    print("V3 models not available")

# Import admin setup
from app.config.admin import setup_admin

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
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Admin Panel
try:
    admin = setup_admin(app)
    print("Admin panel setup successfully at /admin")
except Exception as e:
    print(f"Admin panel setup failed: {e}")

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

# Include V3 API router
app.include_router(api_v3_router, prefix="/api/v3")

# Mount static files for audio and thumbnails
app.mount("/audio", StaticFiles(directory=settings.AUDIO_DIRECTORY), name="audio")
app.mount("/thumbnails", StaticFiles(directory=settings.THUMBNAIL_DIRECTORY), name="thumbnails")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)