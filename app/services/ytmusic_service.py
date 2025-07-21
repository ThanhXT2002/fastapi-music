import requests
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from ytmusicapi import YTMusic

yt = YTMusic()

class YTMusicService:

    def stream_audio(self, song_id):
        import subprocess
        youtube_url = f"https://www.youtube.com/watch?v={song_id}"
        def iterfile():
            # Gọi yt-dlp để stream audio về stdout
            process = subprocess.Popen([
                "yt-dlp",
                "-f", "bestaudio[ext=m4a]/bestaudio/best",
                "-o", "-",  # output to stdout
                youtube_url
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=16*1024)
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

    def search(self, query, filter=None, limit=20):
        results = yt.search(query=query, filter=filter, limit=limit)
        if filter is None:
            # Gom nhóm và sắp xếp: Top result, Artists, Community playlists, các bài hát lẻ (category=null, resultType=song)
            top_result = [item for item in results if item.get('category') == 'Top result']
            artists = [item for item in results if item.get('category') == 'Artists']
            community_playlists = [item for item in results if item.get('category') == 'Community playlists']
            songs_null_category = [item for item in results if item.get('category') is None and item.get('resultType') == 'song']
            return top_result + artists + community_playlists + songs_null_category
        return results

    def get_song(self, song_id):
        result = yt.get_song(song_id)
        audio_url = None
        formats = result.get("streamingData", {}).get("adaptiveFormats", [])
        # Ưu tiên itag 140 (audio/mp4), nếu không có thì lấy audio đầu tiên
        audio_formats = [f for f in formats if f.get("mimeType", "").startswith("audio/")]
        best_audio = next((f for f in audio_formats if f.get("itag") == 140), None) or (audio_formats[0] if audio_formats else None)
        if best_audio:
            if "url" in best_audio:
                audio_url = best_audio["url"]
            elif "signatureCipher" in best_audio:
                from urllib.parse import parse_qs, unquote
                params = parse_qs(best_audio["signatureCipher"])
                audio_url = unquote(params["url"][0])
        result["audio_url"] = audio_url
        return result

    def get_album(self, album_id):
        return yt.get_album(album_id)

    def get_playlist(self, playlist_id):
        return yt.get_playlist(playlist_id)

    def get_artist(self, artist_id):
        return yt.get_artist(artist_id)

    def get_lyrics(self, song_id):
        return yt.get_lyrics(song_id)

    def get_top_songs(self, limit=25, country='ZZ'):
        charts = yt.get_charts(country=country)
        # Kiểm tra dữ liệu trả về
        songs = charts.get('songs')
        if not songs:
            return {"error": "Không có dữ liệu top songs cho quốc gia này"}
        items = songs.get('items')
        if not items or not isinstance(items, list) or len(items) == 0:
            return {"error": "Không có dữ liệu top songs cho quốc gia này"}
        return items[:limit]
