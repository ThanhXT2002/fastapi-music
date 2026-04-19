"""Dang ky tat ca sub-router vao API router chinh.

Module nay chua:
- api_router tong hop tat ca route cua ung dung.
- Endpoint health check.

Lien quan:
- main.py (mount api_router voi prefix /api)
- app/routes/song_routes.py
- app/routes/auth.py
- app/routes/ytmusic_routes.py
"""

# ── Third-party imports ───────────────────────────────────
from fastapi import APIRouter

# ── Internal imports ──────────────────────────────────────
from app.routes.song_routes import router as song_router
from app.routes.auth import router as auth_router
from app.routes.ytmusic_routes import router as ytmusic_router
from app.routes.user import router as user_router


# ── Router ────────────────────────────────────────────────

api_router = APIRouter()

api_router.include_router(song_router)
api_router.include_router(auth_router)
api_router.include_router(ytmusic_router)
api_router.include_router(user_router)


# ── Endpoints ─────────────────────────────────────────────

@api_router.get("/health")
async def health_check():
    """Kiem tra trang thai hoat dong cua API."""
    return {
        "success": True,
        "message": "FastAPI Music is running",
        "version": "3.0.0",
    }
