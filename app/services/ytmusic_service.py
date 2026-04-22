"""
Tương tác với YouTube Music API để tìm kiếm và stream nhạc.

Module này chứa:
- Service tìm kiếm bài hát, album, playlist, nghệ sĩ trên YouTube Music.
- Stream audio trực tiếp từ YouTube (không lưu file lên server).
- Lấy metadata: lời bài hát, bài liên quan, top charts.

Liên quan:
- Service: youtube_service.py (download và lưu trữ file)
"""

# ── Standard library imports ──────────────────────────────
import subprocess
import concurrent.futures

# ── Third-party imports ───────────────────────────────────
from fastapi.responses import StreamingResponse
from ytmusicapi import YTMusic


# ── Module-level instances ────────────────────────────────
# Khởi tạo YTMusic không cần auth — chỉ dùng cho public API
yt = YTMusic()


class YTMusicService:
    """Xử lý tìm kiếm và stream nhạc qua YouTube Music API.

    Chịu trách nhiệm:
        - Tìm kiếm bài hát, album, playlist, nghệ sĩ.
        - Stream audio trực tiếp qua yt-dlp pipe.
        - Lấy metadata: lời bài hát, bài liên quan, top charts.
        - Gợi ý tìm kiếm (search suggestions).

    Không lưu file lên server — chỉ phục vụ nghe nhạc online.
    Sử dụng ytmusicapi (unofficial YouTube Music API) cho metadata
    và yt-dlp CLI cho audio streaming.
    """

    # ── Audio streaming ───────────────────────────────────

    def stream_audio(self, song_id: str) -> StreamingResponse:
        """Stream audio trực tiếp từ YouTube qua yt-dlp pipe.

        Gọi yt-dlp subprocess với output stdout, đọc theo chunk 8KB
        và trả về StreamingResponse cho client. Không lưu file
        trên server — audio được pipe trực tiếp.

        Args:
            song_id: YouTube video ID của bài hát cần stream.

        Returns:
            StreamingResponse với media_type "audio/mp4".
        """
        youtube_url = f"https://www.youtube.com/watch?v={song_id}"

        def iterfile():
            """Generator yield audio chunks tu yt-dlp stdout."""
            process = subprocess.Popen(
                [
                    "yt-dlp",
                    "-f", "bestaudio[ext=m4a]/bestaudio/best",
                    "-o", "-",
                    youtube_url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=16 * 1024
            )
            try:
                while True:
                    chunk = process.stdout.read(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                process.stdout.close()
                process.stderr.close()
                process.terminate()

        return StreamingResponse(iterfile(), media_type="audio/mp4")

    # ── Search ────────────────────────────────────────────

    def search(
        self, query: str, filter: str = None, limit: int = 20
    ) -> list:
        """Tìm kiếm trên YouTube Music.

        Khi filter=None, kết quả được gom nhóm và sắp xếp theo
        thứ tự ưu tiên: Top result -> Artists -> Community playlists
        -> Songs (category=null) để hiển thị phù hợp trên frontend.

        Args:
            query: Từ khóa tìm kiếm.
            filter: Bộ lọc loại kết quả (VD: "songs", "albums",
                "artists"). None để lấy tất cả loại.
            limit: Số lượng kết quả tối đa. Mặc định 20.

        Returns:
            Danh sách kết quả tìm kiếm từ YouTube Music API.
        """
        try:
            results = yt.search(query=query, filter=filter, limit=limit)
        except Exception as e:
            # Fallback: YouTube Music thỉnh thoảng trả về giao diện mới (Top result card)
            # làm ytmusicapi bị lỗi KeyError: 'header'. Ta fallback bằng cách fetch song, artist, album đồng thời.
            if filter is None:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    f_songs = executor.submit(yt.search, query, filter="songs", limit=limit)
                    f_artists = executor.submit(yt.search, query, filter="artists", limit=limit)
                    f_albums = executor.submit(yt.search, query, filter="albums", limit=limit)
                    
                    return f_songs.result() + f_artists.result() + f_albums.result()
            else:
                raise e
        if filter is None:
            # Gom nhom ket qua theo category de frontend hien thi
            top_result = [
                item for item in results
                if item.get('category') == 'Top result'
            ]
            artists = [
                item for item in results
                if item.get('category') == 'Artists'
            ]
            community_playlists = [
                item for item in results
                if item.get('category') == 'Community playlists'
            ]
            songs_null_category = [
                item for item in results
                if item.get('category') is None
                and item.get('resultType') == 'song'
            ]
            return (top_result + artists
                    + community_playlists + songs_null_category)

        return results

    # ── Song details ──────────────────────────────────────

    def get_song(self, song_id: str) -> dict:
        """Lấy thông tin chi tiết một bài hát.

        Args:
            song_id: YouTube video ID.

        Returns:
            Dict chứa metadata bài hát (title, artists, thumbnails...).
        """
        return yt.get_song(song_id)

    def get_playlist_with_song(self, song_id: str) -> dict:
        """Lấy watch playlist (danh sách phát tiếp) từ một bài hát.

        Args:
            song_id: YouTube video ID làm điểm bắt đầu.

        Returns:
            Dict chứa danh sách bài hát sẽ phát tiếp theo.
        """
        return yt.get_watch_playlist(song_id)

    def get_lyrics(self, song_id: str) -> dict:
        """Lấy lời bài hát.

        Args:
            song_id: Browse ID của lyrics (lấy từ get_song hoặc
                get_watch_playlist).

        Returns:
            Dict chứa lời bài hát và nguồn cung cấp.
        """
        return yt.get_lyrics(song_id)

    def get_related_songs(self, browseId: str) -> list:
        """Lấy danh sách bài hát liên quan.

        Args:
            browseId: Browse ID của phần related (lấy từ get_song).

        Returns:
            Danh sách bài hát liên quan.
        """
        return yt.get_song_related(browseId)

    # ── Album & Playlist ──────────────────────────────────

    def get_album(self, album_id: str) -> dict:
        """Lấy thông tin chi tiết một album.

        Args:
            album_id: YouTube Music album ID hoặc browse ID.

        Returns:
            Dict chứa metadata album và danh sách bài hát.
        """
        return yt.get_album(album_id)

    def get_playlist(self, playlist_id: str) -> dict:
        """Lấy thông tin chi tiết một playlist.

        Args:
            playlist_id: YouTube Music playlist ID.

        Returns:
            Dict chứa metadata playlist và danh sách bài hát.
        """
        return yt.get_playlist(playlist_id)

    # ── Artist ────────────────────────────────────────────

    def get_artist(self, artist_id: str) -> dict:
        """Lấy thông tin chi tiết một nghệ sĩ.

        Args:
            artist_id: YouTube Music artist channel ID.

        Returns:
            Dict chứa metadata nghệ sĩ, albums, singles, videos.
        """
        return yt.get_artist(artist_id)

    # ── Charts & Suggestions ──────────────────────────────

    def get_top_songs(self, limit: int = 25, country: str = 'ZZ') -> list:
        """Lấy danh sách top bài hát theo quốc gia.

        Args:
            limit: Số bài hát tối đa. Mặc định 25.
            country: Mã quốc gia ISO 3166-1 alpha-2.
                Mặc định "ZZ" (global charts).

        Returns:
            Danh sách bài hát top charts, hoặc dict chứa
            thông báo lỗi nếu không có dữ liệu.
        """
        # Fallback: yt.get_charts() hien tai bi loi do YouTube doi giao dien.
        # Dung yt.search de lay cac bai hat thinh hanh thay the.
        query = f"Top Trending Songs {country}" if country != 'ZZ' else "Nhạc Việt Hot Trending"
        try:
            results = yt.search(query, filter="songs", limit=limit)
            if not results:
                return [{"error": "Khong co du lieu"}]
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def get_search_suggestions(self, query: str) -> list:
        """Lấy gợi ý tìm kiếm từ YouTube Music.

        Args:
            query: Chuỗi tìm kiếm hiện tại của người dùng.

        Returns:
            Danh sách các gợi ý tìm kiếm liên quan.
        """
        return yt.get_search_suggestions(query)
