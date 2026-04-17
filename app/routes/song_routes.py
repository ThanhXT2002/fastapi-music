"""Route xu ly bai hat: nhan dien, download, streaming, tim kiem.

Module nay chua:
- Endpoint nhan dien bai hat tu file audio (ACRCloud).
- Endpoint lay thong tin va bat dau download tu YouTube.
- Endpoint streaming/download file audio da xu ly.
- Endpoint proxy download truc tiep tu YouTube.
- Endpoint lay thumbnail va danh sach bai hat hoan thanh.

Lien quan:
- Controller: app/controllers/song_controller.py
- Schema:     app/schemas/song.py
- Service:    app/services/youtube_service.py
"""

# ── Standard library imports ──────────────────────────────
from typing import Annotated

# ── Third-party imports ───────────────────────────────────
from fastapi import (
    APIRouter, Depends, BackgroundTasks,
    Response, Query, Request, File, UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# ── Internal imports ──────────────────────────────────────
from app.config.database import get_db
from app.schemas.song import SongInfoRequest, APIResponse
from app.controllers.song_controller import SongController


# ── Router / Dependencies ─────────────────────────────────

router = APIRouter(prefix="/songs", tags=["Songs"])

DBDep = Annotated[Session, Depends(get_db)]


def get_song_controller() -> SongController:
    """Tao instance SongController cho moi request."""
    return SongController()


SongControllerDep = Annotated[
    SongController, Depends(get_song_controller)
]


# ── Endpoints ─────────────────────────────────────────────

@router.post("/identify", response_model=APIResponse)
async def identify_song(
    controller: SongControllerDep,
    file: Annotated[UploadFile, File()],
):
    """Nhan dien bai hat tu file audio upload qua ACRCloud.

    Args:
        controller: Controller xu ly nghiep vu bai hat.
        file: File audio can nhan dien (mp3, wav, m4a...).

    Returns:
        Thong tin bai hat nhan dien duoc (title, artist...).
    """
    file_bytes = await file.read()
    return controller.identify_song_by_file(file_bytes)


@router.post("/info", response_model=APIResponse)
async def get_song_info(
    request_data: SongInfoRequest,
    background_tasks: BackgroundTasks,
    db: DBDep,
    controller: SongControllerDep,
):
    """Lay thong tin bai hat va bat dau download trong background.

    Neu bai hat da ton tai va hoan thanh trong DB, tra ve ngay
    ma khong can download lai.

    Args:
        request_data: Chua youtube_url can xu ly.
        background_tasks: FastAPI background task de download async.
        db: Database session.
        controller: Controller xu ly nghiep vu.

    Returns:
        Metadata bai hat (title, artist, duration, thumbnail...).
    """
    return await controller.get_song_info(
        request_data.youtube_url,
        db,
        background_tasks,
    )


@router.get("/status/{song_id}", response_model=APIResponse)
def get_song_status(
    song_id: str,
    db: DBDep,
    controller: SongControllerDep,
):
    """Lay trang thai xu ly hien tai cua bai hat.

    Args:
        song_id: YouTube video ID.
        db: Database session.
        controller: Controller xu ly nghiep vu.

    Returns:
        Trang thai (pending/processing/completed/failed) va metadata.
    """
    return controller.get_song_status(song_id, db)


@router.get("/download/{song_id}")
async def download_song(
    song_id: str,
    request: Request,
    db: DBDep,
    controller: SongControllerDep,
    download: Annotated[
        bool,
        Query(description="True de download, False de streaming"),
    ] = False,
):
    """Stream hoac download file audio da xu ly.

    Ho tro HTTP Range request cho HTML5 audio seeking.

    Args:
        song_id: YouTube video ID.
        request: HTTP request (can thiet cho Range header).
        db: Database session.
        controller: Controller xu ly nghiep vu.
        download: True de download file, False de streaming inline.

    Returns:
        StreamingResponse voi header Content-Disposition tuong ung.

    Raises:
        HTTP 404: Bai hat khong ton tai hoac chua hoan thanh.
    """
    file_data = await controller.get_audio_file(song_id, db)
    disposition = "attachment" if download else "inline"
    response = await controller.stream_file_with_range(
        request,
        str(file_data["file_path"]),
    )
    response.headers["Content-Disposition"] = (
        f'{disposition}; filename="{file_data["safe_filename"]}"'
    )
    return response


@router.get("/proxy-download/{song_id}")
async def proxy_download(
    song_id: str,
    request: Request,
    db: DBDep,
    controller: SongControllerDep,
):
    """Proxy download audio tu YouTube ve frontend ngay lap tuc.

    Neu file da co tren server (completed) thi serve tu disk.
    Neu chua thi proxy truc tiep tu YouTube — frontend khong can
    cho backend xu ly xong.

    Args:
        song_id: YouTube video ID.
        request: HTTP request.
        db: Database session.
        controller: Controller xu ly nghiep vu.

    Returns:
        StreamingResponse audio.
    """
    return await controller.proxy_download_audio(song_id, request, db)


@router.get("/thumbnail/{song_id}")
async def get_thumbnail(
    song_id: str,
    db: DBDep,
    controller: SongControllerDep,
):
    """Lay thumbnail bai hat tu server hoac proxy tu YouTube.

    Neu file thumbnail da download thanh cong thi stream tu disk.
    Neu chua thi proxy truc tiep tu YouTube URL goc.

    Args:
        song_id: YouTube video ID.
        db: Database session.
        controller: Controller xu ly nghiep vu.

    Returns:
        Response hoac StreamingResponse chua anh thumbnail.
    """
    thumbnail_data = await controller.get_thumbnail_file(song_id, db)

    # Proxy tu YouTube (chua co file tren server)
    if thumbnail_data.get("proxy"):
        return Response(
            content=thumbnail_data["content"],
            media_type=thumbnail_data["media_type"],
            headers={
                'Content-Disposition': (
                    f'inline; filename='
                    f'"{thumbnail_data["safe_filename"]}"'
                ),
                'Cache-Control': 'public, max-age=3600',
            },
        )

    return StreamingResponse(
        controller.file_streamer(thumbnail_data["file_path"]),
        media_type=thumbnail_data["media_type"],
        headers={
            'Content-Disposition': (
                f'inline; filename='
                f'"{thumbnail_data["safe_filename"]}"'
            ),
        },
    )


@router.get("/completed", response_model=APIResponse)
async def get_completed_songs(
    request: Request,
    db: DBDep,
    controller: SongControllerDep,
    limit: Annotated[
        int,
        Query(
            ge=1, le=1000,
            description="So luong bai hat tra ve (1-1000)",
        ),
    ] = 100,
    key: Annotated[
        str | None,
        Query(description="Tu khoa tim kiem fuzzy matching"),
    ] = None,
):
    """Lay danh sach bai hat da hoan thanh voi URL streaming.

    Ho tro tim kiem fuzzy theo title, artist, keywords.

    Args:
        request: HTTP request (dung tao base URL cho streaming).
        db: Database session.
        controller: Controller xu ly nghiep vu.
        limit: So luong bai hat tra ve (1-1000, mac dinh 100).
        key: Tu khoa tim kiem (nullable, fuzzy matching).

    Returns:
        Danh sach bai hat da hoan thanh kem audio_url, thumbnail_url.
    """
    return await controller.get_completed_songs(db, limit, request, key)
