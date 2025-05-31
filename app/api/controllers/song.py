from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.config.database import get_db
from app.internal.storage.repositories.song import SongRepository
from app.internal.utils.youtube_downloader import YouTubeDownloader
from app.api.validators.song import (
    SongResponse, 
    YouTubeDownloadRequest, YouTubeDownloadResponse
)
from app.api.middleware.auth import get_current_user_optional

class SongController:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.song_repo = SongRepository(db)
        self.youtube_downloader = YouTubeDownloader()
    
    def _convert_to_response(self, song) -> SongResponse:
        """Helper method to convert Song model to SongResponse"""
        try:
            return SongResponse(
                id=getattr(song, 'id', str(uuid.uuid4())),
                title=getattr(song, 'title', 'Unknown Title'),
                artist=getattr(song, 'artist', 'Unknown Artist'),
                artists=getattr(song, 'artists', None),
                album=getattr(song, 'album', None),
                duration=getattr(song, 'duration', 0),
                genre=getattr(song, 'genre', None),
                release_date=getattr(song, 'release_date', None),
                thumbnail_url=getattr(song, 'thumbnail_url', None),
                audio_url=getattr(song, 'audio_url', None),
                lyrics=getattr(song, 'lyrics', None),
                has_lyrics=getattr(song, 'has_lyrics', False),
                keywords=getattr(song, 'keywords', None),
                source=getattr(song, 'source', 'youtube'),
                bitrate=getattr(song, 'bitrate', None),
                language=getattr(song, 'language', None),
                is_downloaded=getattr(song, 'is_downloaded', True),
                downloaded_at=getattr(song, 'downloaded_at', None),
                local_path=getattr(song, 'local_path', None),
                is_favorite=getattr(song, 'is_favorite', False),
                play_count=getattr(song, 'play_count', 0),
                last_played_at=getattr(song, 'last_played_at', None),
                user_id=getattr(song, 'user_id', None),
                created_at=getattr(song, 'created_at', datetime.utcnow()),
                updated_at=getattr(song, 'updated_at', datetime.utcnow())
            )
        except Exception as e:
            print(f"Error in _convert_to_response: {e}")
            return SongResponse(
                id=str(uuid.uuid4()),
                title='Unknown Title',
                artist='Unknown Artist',
                duration=0,
                is_downloaded=True,
                downloaded_at=datetime.utcnow(),
                local_path=None,
                is_favorite=False,
                play_count=0,
                last_played_at=None,
                user_id=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    def download_from_youtube(self, request: YouTubeDownloadRequest, current_user = None) -> YouTubeDownloadResponse:
        """Download song from YouTube"""
        try:
            # Check if already downloaded
            existing_song = self.song_repo.find_by_youtube_url(request.url)
            if existing_song:
                return YouTubeDownloadResponse(
                    success=True,
                    message='Song already downloaded',
                    song=self._convert_to_response(existing_song),
                    download_path=existing_song.local_path
                )
            
            # Download from YouTube
            success, result, song_data = self.youtube_downloader.download_audio(request.url)
            
            if not success:
                return YouTubeDownloadResponse(
                    success=False,
                    message=result
                )
            
            # Save to database
            user_id = current_user.id if current_user else None
            song_data['downloaded_at'] = datetime.utcnow()
            song = self.song_repo.create_song(song_data, user_id)
            
            return YouTubeDownloadResponse(
                success=True,
                message='Song downloaded successfully',
                song=self._convert_to_response(song),
                download_path=result
            )
            
        except Exception as e:
            print(f"Error in download_from_youtube: {e}")
            return YouTubeDownloadResponse(
                success=False,
                message=f'Download failed: {str(e)}'
            )
