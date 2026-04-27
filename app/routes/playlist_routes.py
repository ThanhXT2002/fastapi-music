from fastapi import APIRouter
from app.controllers.playlist_controller import router as playlist_router

router = APIRouter()
router.include_router(playlist_router)
