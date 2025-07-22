from fastapi import APIRouter, Query
from app.controllers.ytmusic_controller import YTMusicController

router = APIRouter(prefix="/ytmusic", tags=["ytmusic"])
controller = YTMusicController()

@router.get("/stream/{song_id}")
def stream_audio(song_id: str):
    """
    Proxy stream audio cho FE từ song_id (trả về audio/mp4)
    - song_id: id bài hát/video trên YouTube Music
    Trả về: StreamingResponse audio/mp4
    """
    return controller.stream_audio(song_id)


@router.get("/search")
def search(query: str = Query(...), filter: str = Query(None), limit: int = Query(20)):
    """
    Tìm kiếm bài hát, album, playlist, nghệ sĩ trên YouTube Music.
    - query: từ khóa tìm kiếm
    - filter: loại kết quả, chấp nhận các giá trị:
        'songs' (bài hát),
        'videos' (video),
        'albums' (album),
        'artists' (nghệ sĩ),
        'playlists' (playlist),
        'community_playlists' (playlist cộng đồng),
        'featured_playlists' (playlist nổi bật),
        'uploads' (bài hát đã upload, cần xác thực)
    - limit: số lượng kết quả trả về
    Trả về: list các dict bài hát/album/playlist/nghệ sĩ
    """
    return controller.search(query, filter, limit)


@router.get("/song/{song_id}")
def get_song(song_id: str):
    """
    Lấy thông tin chi tiết một bài hát (metadata, streamingData, videoDetails...)
    - song_id: id bài hát/video trên YouTube Music
    Trả về: dict thông tin bài hát
    """
    return controller.get_song(song_id)


@router.get("/album/{album_id}")
def get_album(album_id: str):
    """
    Lấy thông tin album và danh sách bài hát trong album
    - album_id: id album trên YouTube Music
    Trả về: dict thông tin album, list bài hát
    """
    return controller.get_album(album_id)


@router.get("/playlist/{playlist_id}")
def get_playlist(playlist_id: str):
    """
    Lấy thông tin playlist và danh sách bài hát trong playlist
    - playlist_id: id playlist trên YouTube Music
    Trả về: dict thông tin playlist, list bài hát
    """
    return controller.get_playlist(playlist_id)


@router.get("/artist/{artist_id}")
def get_artist(artist_id: str):
    """
    Lấy thông tin nghệ sĩ, các album, bài hát, video nổi bật
    - artist_id: id kênh nghệ sĩ trên YouTube Music
    Trả về: dict thông tin nghệ sĩ, list album, list bài hát
    """
    return controller.get_artist(artist_id)


@router.get("/song/{song_id}/lyrics")
def get_lyrics(song_id: str):
    """
    Lấy lyrics của bài hát
    - song_id: id bài hát/video trên YouTube Music
    Trả về: dict lyrics, source, hasTimestamps
    """
    return controller.get_lyrics(song_id)

@router.get("/related/{browseId}")
def get_related_songs(browseId: str):
    """
    Lấy các nội dung liên quan đến bài hát (playlist, nghệ sĩ, bài hát tương tự...)
    - browseId: id duyệt bài hát/playlist trên YouTube Music
    Trả về: list các nội dung liên quan
    """
    return controller.get_related_songs(browseId)



@router.get("/top-songs")
def get_top_songs(limit: int = Query(25), country: str = Query('ZZ')):
    """
    Lấy danh sách các bài hát thịnh hành (top songs) theo quốc gia
    - limit: số lượng bài hát trả về
    - country: mã quốc gia (ZZ: toàn cầu, VN: Việt Nam, US: Mỹ...)
    Trả về: list dict bài hát thịnh hành hoặc thông báo lỗi nếu không có dữ liệu
    """
    return controller.get_top_songs(limit=limit, country=country)
