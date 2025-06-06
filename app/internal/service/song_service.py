from typing import List, Optional
from sqlalchemy.orm import Session
from app.internal.storage.repositories.song import SongRepository
from app.api.validators.song import SongBase, SongResponse
from app.internal.domain.song import Song
from fastapi import HTTPException, status

class SongService:
    def __init__(self, db: Session):
        self.song_repo = SongRepository(db)

    def create_song(self, song_data: SongBase, user_id: Optional[int] = None) -> SongResponse:
        """Create a new song"""
        try:
            song_dict = song_data.model_dump()
            song = self.song_repo.create_song(song_dict, user_id)
            return self._convert_to_response(song)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating song: {str(e)}"
            )

    def get_song(self, song_id: str) -> SongResponse:
        """Get song by ID"""
        song = self.song_repo.get_by_id(song_id)
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        return self._convert_to_response(song)

    def get_all_songs(self, skip: int = 0, limit: int = 100) -> List[SongResponse]:
        """Get all songs"""
        songs = self.song_repo.get_all(skip=skip, limit=limit)
        return [self._convert_to_response(song) for song in songs]

    def get_user_songs(self, user_id: int, skip: int = 0, limit: int = 100) -> List[SongResponse]:
        """Get songs of a specific user"""
        try:
            from app.internal.domain.user import User
            user = self.song_repo.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get songs from many-to-many relationship
            songs = user.songs[skip:skip + limit]
            return [self._convert_to_response(song) for song in songs]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting user songs: {str(e)}"
            )

    def update_song(self, song_id: str, song_data: dict) -> SongResponse:
        """Update song"""
        song = self.song_repo.get_by_id(song_id)
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        # Convert keywords to JSON string if it's a list
        if 'keywords' in song_data and isinstance(song_data['keywords'], list):
            import json
            song_data['keywords'] = json.dumps(song_data['keywords'])
        
        updated_song = self.song_repo.update(song_id, song_data)
        return self._convert_to_response(updated_song)

    def delete_song(self, song_id: str) -> dict:
        """Delete song"""
        if not self.song_repo.delete(song_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        return {"message": "Song deleted successfully"}

    def add_user_to_song(self, song_id: str, user_id: int) -> SongResponse:
        """Add user to song"""
        song = self.song_repo.get_by_id(song_id)
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        from app.internal.domain.user import User
        user = self.song_repo.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user not in song.users:
            song.users.append(user)
            self.song_repo.db.commit()
            self.song_repo.db.refresh(song)
        
        return self._convert_to_response(song)

    def remove_user_from_song(self, song_id: str, user_id: int) -> SongResponse:
        """Remove user from song"""
        song = self.song_repo.get_by_id(song_id)
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        from app.internal.domain.user import User
        user = self.song_repo.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user in song.users:
            song.users.remove(user)
            self.song_repo.db.commit()
            self.song_repo.db.refresh(song)
        
        return self._convert_to_response(song)

    def toggle_favorite(self, song_id: str) -> SongResponse:
        """Toggle favorite status"""
        song = self.song_repo.get_by_id(song_id)
        if not song:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Song not found"
            )
        
        song.is_favorite = not song.is_favorite
        self.song_repo.db.commit()
        self.song_repo.db.refresh(song)
        return self._convert_to_response(song)

    def _convert_to_response(self, song: Song) -> SongResponse:
        """Convert Song model to SongResponse"""
        return SongResponse(
            id=song.id,
            title=song.title,
            artist=song.artist,
            album=song.album,
            duration=song.duration,
            thumbnail_url=song.thumbnail_url,
            audio_url=song.audio_url,
            local_path=song.local_path,
            is_favorite=song.is_favorite,
            keywords=song.keywords,
            source_url=song.source_url,
            created_at=song.created_at,
            updated_at=song.updated_at
        )
