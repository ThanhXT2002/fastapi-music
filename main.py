"""Entrypoint ung dung FastAPI Music.

Module nay chua:
- Khai bao FastAPI app voi lifespan (startup/shutdown).
- Cau hinh CORS middleware.
- Mount router va static files.

Lien quan:
- Router:   app/routes/router.py
- Config:   app/config/config.py
- Database: app/config/database.py
"""

# ── Standard library imports ──────────────────────────────
from contextlib import asynccontextmanager

# ── Third-party imports ───────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Internal imports ──────────────────────────────────────
from app.routes.router import api_router
from app.config.config import settings
from app.config.database import create_tables, get_database_info

# Import model de SQLAlchemy dang ky metadata truoc create_tables()
from app.models.user import User  # noqa: F401
from app.models.song import Song  # noqa: F401
from app.models.playlist import Playlist, PlaylistSong  # noqa: F401


# ── Lifespan ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quan ly lifecycle cua ung dung (startup va shutdown).

    Startup:
        - Tao cac bang database neu chua ton tai.
        - In thong tin ket noi database ra console.

    Shutdown:
        - Hien tai chua co logic cleanup.
    """
    try:
        create_tables()
        db_info = get_database_info()
        print(f"Database connected successfully")
        print(f"Database type: {db_info['database_type']}")
        if db_info.get('database_file'):
            print(f"Database file: {db_info['database_file']}")
    except Exception as e:
        print(f"Database connection failed: {e}")

    yield


# ── App instance ──────────────────────────────────────────

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

app.mount(
    "/audio",
    StaticFiles(directory=settings.AUDIO_DIRECTORY),
    name="audio",
)
app.mount(
    "/thumbnails",
    StaticFiles(directory=settings.THUMBNAIL_DIRECTORY),
    name="thumbnails",
)


# ── Endpoints ─────────────────────────────────────────────

@app.get("/test")
async def serve_test():
    """Phuc vu trang HTML test streaming audio (chi dung khi dev)."""
    from fastapi.responses import FileResponse
    return FileResponse("test_streaming.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)