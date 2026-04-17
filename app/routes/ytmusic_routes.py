"""Route tuong tac voi YouTube Music API.

Module nay chua:
- Endpoint streaming audio truc tiep tu YouTube.
- Endpoint tim kiem bai hat, album, playlist, nghe si.
- Endpoint lay metadata: loi bai hat, bai lien quan, top charts.
- Endpoint goi y tim kiem.

Lien quan:
- Controller: app/controllers/ytmusic_controller.py
- Service:    app/services/ytmusic_service.py
"""

# ── Standard library imports ──────────────────────────────
from typing import Annotated

# ── Third-party imports ───────────────────────────────────
from fastapi import APIRouter, Depends, Query

# ── Internal imports ──────────────────────────────────────
from app.controllers.ytmusic_controller import YTMusicController


# ── Router / Dependencies ─────────────────────────────────

router = APIRouter(prefix="/ytmusic", tags=["ytmusic"])


def get_ytmusic_controller() -> YTMusicController:
    """Tao instance YTMusicController cho moi request."""
    return YTMusicController()


YTMusicControllerDep = Annotated[
    YTMusicController, Depends(get_ytmusic_controller)
]


# ── Endpoints ─────────────────────────────────────────────

@router.get("/stream/{song_id}")
def stream_audio(
    song_id: str,
    controller: YTMusicControllerDep,
):
    """Stream audio truc tiep tu YouTube qua yt-dlp pipe.

    Audio duoc pipe truc tiep tu YouTube, khong luu file tren server.

    Args:
        song_id: YouTube video ID.
        controller: Controller xu ly nghiep vu.

    Returns:
        StreamingResponse voi media_type audio/mp4.
    """
    return controller.stream_audio(song_id)


@router.get("/search")
def search(
    controller: YTMusicControllerDep,
    query: Annotated[str, Query()],
    filter: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query()] = 20,
):
    """Tim kiem bai hat, album, playlist, nghe si tren YouTube Music.

    Khi filter=None, ket qua duoc gom nhom va sap xep theo
    thu tu uu tien de hien thi phu hop tren frontend.

    Args:
        controller: Controller xu ly nghiep vu.
        query: Tu khoa tim kiem.
        filter: Bo loc loai ket qua (songs, videos, albums,
            artists, playlists...). None de lay tat ca.
        limit: So luong ket qua toi da. Mac dinh 20.

    Returns:
        Danh sach ket qua tim kiem tu YouTube Music API.
    """
    return controller.search(query, filter, limit)


@router.get("/song/{song_id}")
def get_song(
    song_id: str,
    controller: YTMusicControllerDep,
):
    """Lay thong tin chi tiet mot bai hat.

    Args:
        song_id: YouTube video ID.
        controller: Controller xu ly nghiep vu.

    Returns:
        Dict chua metadata bai hat (title, artists, thumbnails...).
    """
    return controller.get_song(song_id)


@router.get("/playlist-with-song/{song_id}")
def get_playlist_with_song(
    song_id: str,
    controller: YTMusicControllerDep,
):
    """Lay watch playlist (danh sach phat tiep) tu mot bai hat.

    Args:
        song_id: YouTube video ID lam diem bat dau.
        controller: Controller xu ly nghiep vu.

    Returns:
        Dict chua danh sach bai hat se phat tiep theo.
    """
    return controller.get_playlist_with_song(song_id)


@router.get("/album/{album_id}")
def get_album(
    album_id: str,
    controller: YTMusicControllerDep,
):
    """Lay thong tin chi tiet album va danh sach bai hat.

    Args:
        album_id: YouTube Music album ID hoac browse ID.
        controller: Controller xu ly nghiep vu.

    Returns:
        Dict chua metadata album va danh sach bai hat.
    """
    return controller.get_album(album_id)


@router.get("/playlist/{playlist_id}")
def get_playlist(
    playlist_id: str,
    controller: YTMusicControllerDep,
):
    """Lay thong tin chi tiet playlist va danh sach bai hat.

    Args:
        playlist_id: YouTube Music playlist ID.
        controller: Controller xu ly nghiep vu.

    Returns:
        Dict chua metadata playlist va danh sach bai hat.
    """
    return controller.get_playlist(playlist_id)


@router.get("/artist/{artist_id}")
def get_artist(
    artist_id: str,
    controller: YTMusicControllerDep,
):
    """Lay thong tin chi tiet nghe si va cac noi dung noi bat.

    Args:
        artist_id: YouTube Music artist channel ID.
        controller: Controller xu ly nghiep vu.

    Returns:
        Dict chua metadata nghe si, albums, singles, videos.
    """
    return controller.get_artist(artist_id)


@router.get("/song/{song_id}/lyrics")
def get_lyrics(
    song_id: str,
    controller: YTMusicControllerDep,
):
    """Lay loi bai hat.

    Args:
        song_id: YouTube video ID.
        controller: Controller xu ly nghiep vu.

    Returns:
        Dict chua loi bai hat, nguon cung cap, va timestamps.
    """
    return controller.get_lyrics(song_id)


@router.get("/related/{browseId}")
def get_related_songs(
    browseId: str,
    controller: YTMusicControllerDep,
):
    """Lay danh sach noi dung lien quan den bai hat.

    Args:
        browseId: Browse ID cua phan related (lay tu get_song).
        controller: Controller xu ly nghiep vu.

    Returns:
        Danh sach bai hat, playlist, nghe si lien quan.
    """
    return controller.get_related_songs(browseId)


@router.get("/top-songs")
def get_top_songs(
    controller: YTMusicControllerDep,
    limit: Annotated[int, Query()] = 25,
    country: Annotated[str, Query()] = 'ZZ',
):
    """Lay danh sach bai hat thinh hanh theo quoc gia.

    Args:
        controller: Controller xu ly nghiep vu.
        limit: So bai hat toi da. Mac dinh 25.
        country: Ma quoc gia ISO 3166-1 alpha-2.
            Mac dinh "ZZ" (global charts).

    Returns:
        Danh sach bai hat top charts, hoac dict loi
        neu khong co du lieu.
    """
    return controller.get_top_songs(limit=limit, country=country)


@router.get("/search-suggestions")
def get_search_suggestions(
    query: Annotated[str, Query()],
    controller: YTMusicControllerDep,
):
    """Lay goi y tim kiem tu YouTube Music.

    Args:
        query: Chuoi tim kiem hien tai cua nguoi dung.
        controller: Controller xu ly nghiep vu.

    Returns:
        Danh sach cac goi y tim kiem lien quan.
    """
    return controller.get_search_suggestions(query)