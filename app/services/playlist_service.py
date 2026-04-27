from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.playlist import Playlist, PlaylistSong
from app.schemas.playlist import PlaylistCreate, PlaylistResponse

class PlaylistService:
    def __init__(self, db: Session):
        self._db = db

    def get_user_playlists(self, user_id: str) -> list[PlaylistResponse]:
        """Lấy danh sách playlist của người dùng."""
        # Query playlists and count songs
        results = self._db.query(
            Playlist,
            func.count(PlaylistSong.song_id).label("track_count")
        ).outerjoin(PlaylistSong).filter(Playlist.user_id == user_id).group_by(Playlist.id).all()

        response = []
        for playlist, count in results:
            response.append(PlaylistResponse(
                id=playlist.id,
                title=playlist.name,
                ownerId=playlist.user_id,
                ownerName="Bạn",  # Tạm hardcode, thực tế lấy từ user profile
                trackCount=count,
                isPublic=playlist.is_public,
                createdAt=playlist.created_at.isoformat(),
                updatedAt=playlist.updated_at.isoformat()
            ))
        return response

    def create_playlist(self, user_id: str, data: PlaylistCreate) -> PlaylistResponse:
        """Tạo playlist mới."""
        playlist = Playlist(
            id=data.id,
            name=data.title,
            user_id=user_id,
            is_public=data.isPublic
        )
        self._db.add(playlist)
        self._db.commit()
        self._db.refresh(playlist)

        return PlaylistResponse(
            id=playlist.id,
            title=playlist.name,
            ownerId=playlist.user_id,
            ownerName="Bạn",
            trackCount=0,
            isPublic=playlist.is_public,
            createdAt=playlist.created_at.isoformat(),
            updatedAt=playlist.updated_at.isoformat()
        )

    def add_track_to_playlist(self, user_id: str, playlist_id: str, track_id: str) -> None:
        """Thêm bài hát vào playlist."""
        # Check ownership
        playlist = self._db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == user_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found or permission denied")
        
        # Check if already exists
        existing = self._db.query(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == track_id).first()
        if existing:
            return  # Already added

        song = PlaylistSong(playlist_id=playlist_id, song_id=track_id)
        self._db.add(song)
        self._db.commit()

    def remove_track_from_playlist(self, user_id: str, playlist_id: str, track_id: str) -> None:
        """Xoá bài hát khỏi playlist."""
        playlist = self._db.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == user_id).first()
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found or permission denied")
            
        song = self._db.query(PlaylistSong).filter(PlaylistSong.playlist_id == playlist_id, PlaylistSong.song_id == track_id).first()
        if song:
            self._db.delete(song)
            self._db.commit()
