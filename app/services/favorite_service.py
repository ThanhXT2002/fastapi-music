"""Dich vu xu ly logic yeu thich bai hat (Favorite).

Module nay cung cap cac ham de them, xoa va lay danh sach bai hat 
yeu thich cua mot nguoi dung cu special.
"""

# ── Standard library imports ──────────────────────────────
from fastapi import HTTPException, Request

# ── Third-party imports ───────────────────────────────────
from sqlalchemy.orm import Session
from sqlalchemy import desc

# ── Internal imports ──────────────────────────────────────
from app.models.user_songs import UserSong
from app.models.song import Song, ProcessingStatus
from app.schemas.song import CompletedSongResponse, CompletedSongsListResponse
from app.schemas.base import ApiResponse
from app.config.config import settings


class FavoriteService:
    """Service quan ly danh sach bai hat yeu thich cua nguoi dung."""

    def __init__(self):
        pass

    def get_domain_url(self, request: Request) -> str:
        """Lay base URL de tao link audio va thumbnail."""
        try:
            forwarded_proto = request.headers.get('x-forwarded-proto')
            forwarded_host = request.headers.get('x-forwarded-host')

            if forwarded_proto and forwarded_host:
                return f"{forwarded_proto}://{forwarded_host}"

            host = request.headers.get('host')
            if host:
                if 'https' in str(request.url) or request.headers.get('x-forwarded-proto') == 'https':
                    return f"https://{host}"
                return f"http://{host}"

            return str(request.base_url).rstrip('/')
        except Exception:
            return settings.BASE_URL

    def add_favorite(self, user_id: str, song_id: str, db: Session) -> ApiResponse:
        """Them bai hat vao danh sach yeu thich.

        Args:
            user_id: Firebase UID.
            song_id: YouTube Video ID.
            db: Database session.

        Returns:
            ApiResponse thong bao thanh cong.
        """
        # Kiem tra bai hat ton tai khong
        song = db.query(Song).filter(Song.id == song_id).first()
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")

        # Kiem tra xem da them chua
        existing = db.query(UserSong).filter(
            UserSong.user_id == user_id, 
            UserSong.song_id == song_id
        ).first()

        if existing:
            return ApiResponse.ok(message="Song is already in favorites")

        # Them vao DB
        user_song = UserSong(user_id=user_id, song_id=song_id)
        db.add(user_song)
        db.commit()

        return ApiResponse.ok(message="Song added to favorites")

    def remove_favorite(self, user_id: str, song_id: str, db: Session) -> ApiResponse:
        """Xoa bai hat khoi danh sach yeu thich.

        Args:
            user_id: Firebase UID.
            song_id: YouTube Video ID.
            db: Database session.

        Returns:
            ApiResponse thong bao thanh cong.
        """
        existing = db.query(UserSong).filter(
            UserSong.user_id == user_id, 
            UserSong.song_id == song_id
        ).first()

        if not existing:
            return ApiResponse.ok(message="Song is not in favorites")

        db.delete(existing)
        db.commit()

        return ApiResponse.ok(message="Song removed from favorites")

    def get_user_favorites(
        self, user_id: str, db: Session, limit: int = 100, request: Request = None
    ) -> ApiResponse:
        """Lay danh sach chi tiet bai hat yeu thich cua nguoi dung.

        Tra ve day du thong tin bai hat giong nhu tim kiem de hien thi tren UI.
        """
        user_songs = db.query(UserSong).filter(
            UserSong.user_id == user_id
        ).order_by(desc(UserSong.created_at)).limit(limit).all()

        song_ids = [us.song_id for us in user_songs]

        # Lay chi tiet cac bai hat (chi lay cac bai hat da xu ly xong hoac dang co san)
        songs = db.query(Song).filter(
            Song.id.in_(song_ids),
            Song.status == ProcessingStatus.COMPLETED
        ).all()

        # Tao dictionary de preserve thu tu cua user_songs (moi nhat truoc)
        song_dict = {song.id: song for song in songs}
        
        songs_data = []
        base_url = self.get_domain_url(request) if request else settings.BASE_URL

        for us in user_songs:
            song = song_dict.get(us.song_id)
            if song:
                audio_url = f"{base_url}/api/songs/download/{song.id}"
                thumbnail_url = f"{base_url}/api/songs/thumbnail/{song.id}"
                keywords = [k.strip() for k in song.keywords.split(',') if k.strip()] if song.keywords else []
                
                song_data = CompletedSongResponse(
                    id=song.id,
                    title=song.title,
                    artist=song.artist,
                    duration=song.duration,
                    duration_formatted=song.duration_formatted,
                    thumbnail_url=thumbnail_url,
                    audio_url=audio_url,
                    keywords=keywords
                )
                songs_data.append(song_data)

        response_data = CompletedSongsListResponse(
            songs=songs_data,
            total=len(songs_data)
        )

        return ApiResponse.ok(
            data=response_data.model_dump(),
            message="Retrieved favorite songs"
        )

    def get_favorite_ids(self, user_id: str, db: Session) -> ApiResponse:
        """Lay danh sach cac ID bai hat yeu thich cua nguoi dung.
        
        Dung de dong bo nhanh trang thai "Heart" tren UI ma khong can tai toan bo data.
        """
        user_songs = db.query(UserSong).filter(UserSong.user_id == user_id).all()
        song_ids = [us.song_id for us in user_songs]

        return ApiResponse.ok(
            data=song_ids,
            message="Retrieved favorite song IDs"
        )
