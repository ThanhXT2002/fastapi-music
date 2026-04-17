"""Controller dieu phoi cac thao tac voi YouTube Music API.

Module nay chua:
- YTMusicController: lop trung gian giua route va YTMusicService,
  xu ly exception va chuyen thanh HTTPException.

Lien quan:
- Route:   app/routes/ytmusic_routes.py
- Service: app/services/ytmusic_service.py
"""

# ── Third-party imports ───────────────────────────────────
from fastapi import HTTPException

# ── Internal imports ──────────────────────────────────────
from app.services.ytmusic_service import YTMusicService

# Instance dung chung — YTMusicService la stateless
yt_service = YTMusicService()


class YTMusicController:
    """Dieu phoi request tu route xuong YTMusicService.

    Moi method boc service call trong try/except de chuyen
    exception thanh HTTP 500 response.
    """

    def get_search_suggestions(self, query: str):
        """Lay goi y tim kiem tu YouTube Music.

        Args:
            query: Tu khoa nguoi dung dang nhap.

        Returns:
            Danh sach goi y tim kiem.
        """
        try:
            return yt_service.get_search_suggestions(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_related_songs(self, browseId: str):
        """Lay noi dung lien quan den bai hat.

        Args:
            browseId: Browse ID cua phan related.

        Returns:
            Danh sach bai hat, playlist, nghe si lien quan.
        """
        try:
            return yt_service.get_related_songs(browseId)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def stream_audio(self, song_id: str):
        """Stream audio tu YouTube qua yt-dlp pipe.

        Args:
            song_id: YouTube video ID.

        Returns:
            StreamingResponse audio/mp4.
        """
        try:
            return yt_service.stream_audio(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def search(
        self, query: str, filter: str | None = None, limit: int = 20
    ):
        """Tim kiem bai hat, album, playlist, nghe si.

        Args:
            query: Tu khoa tim kiem.
            filter: Bo loc loai ket qua (nullable).
            limit: So ket qua toi da.

        Returns:
            Danh sach ket qua tim kiem.
        """
        try:
            return yt_service.search(query, filter, limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_song(self, song_id: str):
        """Lay thong tin chi tiet mot bai hat.

        Args:
            song_id: YouTube video ID.

        Returns:
            Dict metadata bai hat.
        """
        try:
            return yt_service.get_song(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_album(self, album_id: str):
        """Lay thong tin album va danh sach bai hat.

        Args:
            album_id: YouTube Music album ID.

        Returns:
            Dict metadata album va tracks.
        """
        try:
            return yt_service.get_album(album_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_playlist(self, playlist_id: str):
        """Lay thong tin playlist va danh sach bai hat.

        Args:
            playlist_id: YouTube Music playlist ID.

        Returns:
            Dict metadata playlist va tracks.
        """
        try:
            return yt_service.get_playlist(playlist_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_artist(self, artist_id: str):
        """Lay thong tin chi tiet nghe si va noi dung noi bat.

        Args:
            artist_id: YouTube Music artist channel ID.

        Returns:
            Dict metadata nghe si, albums, singles, videos.
        """
        try:
            return yt_service.get_artist(artist_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_lyrics(self, song_id: str):
        """Lay loi bai hat.

        Args:
            song_id: YouTube video ID.

        Returns:
            Dict loi bai hat, nguon, timestamps.
        """
        try:
            return yt_service.get_lyrics(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_top_songs(self, limit: int = 25, country: str = 'ZZ'):
        """Lay danh sach bai hat thinh hanh theo quoc gia.

        Args:
            limit: So bai hat toi da.
            country: Ma quoc gia ISO 3166-1 alpha-2.

        Returns:
            Danh sach top charts hoac dict loi.
        """
        try:
            return yt_service.get_top_songs(
                limit=limit, country=country
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_playlist_with_song(self, song_id: str):
        """Lay watch playlist (danh sach phat tiep) tu bai hat.

        Args:
            song_id: YouTube video ID lam diem bat dau.

        Returns:
            Dict danh sach bai hat se phat tiep theo.
        """
        try:
            return yt_service.get_playlist_with_song(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
