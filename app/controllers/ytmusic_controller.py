from app.services.ytmusic_service import YTMusicService
from fastapi import HTTPException

yt_service = YTMusicService()

class YTMusicController:

    def get_search_suggestions(self, query):
        try:
            return yt_service.get_search_suggestions(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_related_songs(self, browseId):
        try:
            return yt_service.get_related_songs(browseId)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def stream_audio(self, song_id):
        try:
            return yt_service.stream_audio(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    def search(self, query, filter=None, limit=20):
        try:
            return yt_service.search(query, filter, limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_song(self, song_id):
        try:
            return yt_service.get_song(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_album(self, album_id):
        try:
            return yt_service.get_album(album_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_playlist(self, playlist_id):
        try:
            return yt_service.get_playlist(playlist_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_artist(self, artist_id):
        try:
            return yt_service.get_artist(artist_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_lyrics(self, song_id):
        try:
            return yt_service.get_lyrics(song_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_top_songs(self, limit=25, country='ZZ'):
        try:
            return yt_service.get_top_songs(limit=limit, country=country)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_playlist_with_song(self, song_id: str):
        try:
            return yt_service.get_playlist_with_song(song_id)
        except Exception as e:
            # Có thể mở rộng để trả về các mã lỗi khác nhau tùy loại lỗi
            raise HTTPException(status_code=500, detail=str(e))
        
    
