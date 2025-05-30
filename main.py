from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path
from app.api.routes.router import api_router
from app.config.config import settings
from app.config.database import Base, engine

# Import models to ensure they are registered with SQLAlchemy
from app.internal.domain.user import User
from app.internal.domain.song import Song

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Create upload directories
Path(settings.UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)
Path(settings.AUDIO_DIRECTORY).mkdir(parents=True, exist_ok=True)
Path(settings.THUMBNAIL_DIRECTORY).mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIRECTORY), name="uploads")
 
# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)