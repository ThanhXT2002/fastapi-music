from fastapi import Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from app.config.database import get_db
from app.internal.storage.repositories.song import SongRepository
from app.internal.utils.youtube_downloader import YouTubeDownloader
from app.api.validators.song import (
    SongCreate, SongUpdate, SongResponse, 
    YouTubeDownloadRequest, YouTubeDownloadResponse,
    SongSyncRequest, SongSyncResponse
)
from app.api.middleware.auth import get_current_user_optional, get_current_user

class SongController:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.song_repo = SongRepository(db)
        self.youtube_downloader = YouTubeDownloader()
    
    def get_songs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        current_user = None
    ) -> List[SongResponse]:
        """Get songs - user songs if authenticated, public songs if not"""
        user_id = current_user.id if current_user else None
        
        if user_id:
            songs = self.song_repo.find_by_user(user_id, skip, limit)
        else:
            # Return public songs (songs without user_id)
            songs = self.song_repo.db.query(self.song_repo.model).filter(
                self.song_repo.model.user_id.is_(None)
            ).offset(skip).limit(limit).all()
        
        return [self._convert_to_response(song) for song in songs]
    
    def get_song(self, song_id: str, current_user = None) -> SongResponse:
        """Get single song"""
        song = self.song_repo.find_by_id(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Check access rights
        if song.user_id and (not current_user or song.user_id != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return self._convert_to_response(song)
    
    def create_song(self, song_data: SongCreate, current_user) -> SongResponse:
        """Create new song (authenticated users only)"""
        song_dict = song_data.dict()
        song = self.song_repo.create_song(song_dict, current_user.id)
        return self._convert_to_response(song)
      def update_song(
        self, 
        song_id: str, 
        song_data: SongUpdate, 
        current_user
    ) -> SongResponse:
        """Update song (owner only)"""
        song = self.song_repo.find_by_id(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        if song.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        update_data = song_data.dict(exclude_unset=True)
        
        # Convert list fields to JSON strings
        if 'artists' in update_data and update_data['artists']:
            update_data['artists'] = json.dumps(update_data['artists'])
        if 'genre' in update_data and update_data['genre']:
            update_data['genre'] = json.dumps(update_data['genre'])
        if 'keywords' in update_data and update_data['keywords']:
            update_data['keywords'] = json.dumps(update_data['keywords'])
        
        updated_song = self.song_repo.update(song_id, update_data)
        return self._convert_to_response(updated_song)
    
    def delete_song(self, song_id: str, current_user) -> dict:
        """Delete song (owner only)"""
        song = self.song_repo.find_by_id(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        if song.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = self.song_repo.delete(song_id)
        if success:
            return {"message": "Song deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete song")
      def download_from_youtube(
        self, 
        request: YouTubeDownloadRequest,
        current_user = None
    ) -> YouTubeDownloadResponse:
        """Download song from YouTube"""
        try:
            # Check if already downloaded
            existing_song = self.song_repo.find_by_youtube_url(request.url)
            if existing_song:
                return YouTubeDownloadResponse(
                    success=True,
                    message="Song already downloaded",
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
                message="Song downloaded successfully",
                song=self._convert_to_response(song),
                download_path=result
            )
            
        except Exception as e:
            return YouTubeDownloadResponse(
                success=False,
                message=f"Download failed: {str(e)}"
            )
      def sync_songs(
        self, 
        request: SongSyncRequest, 
        current_user
    ) -> SongSyncResponse:
        """Sync songs from frontend for authenticated user"""
        try:
            songs_data = [song.dict() for song in request.songs]
            created_songs = self.song_repo.bulk_create_songs(songs_data, current_user.id)
            
            synced_count = len(created_songs)
            failed_count = len(songs_data) - synced_count
            
            return SongSyncResponse(
                success=True,
                message=f"Synced {synced_count} songs successfully",
                synced_count=synced_count,
                failed_count=failed_count
            )
            
        except Exception as e:
            return SongSyncResponse(
                success=False,
                message=f"Sync failed: {str(e)}",
                synced_count=0,
                failed_count=len(request.songs),
                errors=[str(e)]
            )
      def search_songs(
        self,
        q: str, 
        skip: int = 0, 
        limit: int = 50,
        current_user = None
    ) -> List[SongResponse]:
        """Search songs"""
        user_id = current_user.id if current_user else None
        songs = self.song_repo.search_songs(q, user_id, skip, limit)
        return [self._convert_to_response(song) for song in songs]
    
    def get_favorites(self, current_user) -> List[SongResponse]:
        """Get user's favorite songs"""
        songs = self.song_repo.find_favorites_by_user(current_user.id)
        return [self._convert_to_response(song) for song in songs]
    
    def toggle_favorite(self, song_id: str, current_user) -> SongResponse:
        """Toggle favorite status"""
        song = self.song_repo.find_by_id(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        if song.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        updated_song = self.song_repo.toggle_favorite(song_id)
        return self._convert_to_response(updated_song)
    
    def play_song(self, song_id: str, current_user = None) -> SongResponse:
        """Play song (increment play count)"""
        song = self.song_repo.find_by_id(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        # Check access rights
        if song.user_id and (not current_user or song.user_id != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        updated_song = self.song_repo.update_play_count(song_id)
        return self._convert_to_response(updated_song)
    
    def get_recently_played(self, current_user) -> List[SongResponse]:
        """Get recently played songs"""
        songs = self.song_repo.get_recently_played(current_user.id)
        return [self._convert_to_response(song) for song in songs]
    
    def _convert_to_response(self, song) -> SongResponse:
        """Convert Song model to SongResponse"""
        song_dict = {
            'id': song.id,
            'title': song.title,
            'artist': song.artist,
            'artists': json.loads(song.artists) if song.artists else None,
            'album': song.album,
            'duration': song.duration,
            'genre': json.loads(song.genre) if song.genre else None,
            'release_date': song.release_date,
            'thumbnail_url': song.thumbnail_url,
            'audio_url': song.audio_url,
            'lyrics': song.lyrics,
            'has_lyrics': song.has_lyrics,
            'is_downloaded': song.is_downloaded,
            'downloaded_at': song.downloaded_at,
            'local_path': song.local_path,
            'is_favorite': song.is_favorite,
            'play_count': song.play_count,
            'last_played_at': song.last_played_at,
            'keywords': json.loads(song.keywords) if song.keywords else None,
            'source': song.source,
            'bitrate': song.bitrate,
            'language': song.language,
            'user_id': song.user_id,
            'created_at': song.created_at,
            'updated_at': song.updated_at
        }
        return SongResponse(**song_dict)
