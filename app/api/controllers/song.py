from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import re  
import json
import os
import asyncio
import threading
import traceback
from app.config.config import settings

from app.config.database import get_db
from app.internal.storage.repositories.song import SongRepository
from app.internal.utils.youtube_downloader import YouTubeDownloader
from app.internal.utils.cloudinary_service import CloudinaryService
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
        self.cloudinary_service = CloudinaryService()
    
    def _convert_to_response(self, song) -> SongResponse:
        """Helper method to convert Song model to SongResponse"""
        try:
            # Parse JSON fields if they exist (keep as string for Pydantic)
            keywords = getattr(song, 'keywords', None)
            # Don't parse to list here - keep as JSON string for Pydantic validator
            
            # Helper function to convert local file paths to serving URLs
            def make_serving_url(local_path):
                if not local_path:
                    return None
                if local_path.startswith('http'):
                    return local_path
                
                # Convert full file path to relative URL path
                base_url = settings.BASE_URL.rstrip('/')
                
                # Extract filename from full path
                import os
                filename = os.path.basename(local_path)
                
                # Determine if it's audio or thumbnail based on path
                if 'audio' in local_path.lower():
                    return f"{base_url}/uploads/audio/{filename}"
                elif 'thumbnail' in local_path.lower():
                    return f"{base_url}/uploads/thumbnails/{filename}"
                else:
                    return None
            
            # Prioritize Cloudinary URLs for existing songs, local paths for new ones
            thumbnail_url = getattr(song, 'thumbnail_url_cloudinary', None) or make_serving_url(getattr(song, 'thumbnail_local_path', None))
            audio_url = getattr(song, 'audio_url_cloudinary', None) or make_serving_url(getattr(song, 'audio_local_path', None))
            
            return SongResponse.model_validate({
                'id': getattr(song, 'id', str(uuid.uuid4())),
                'title': getattr(song, 'title', 'Unknown Title'),
                'artist': getattr(song, 'artist', 'Unknown Artist'),
                'album': getattr(song, 'album', None),
                'duration': getattr(song, 'duration', 0),
                'thumbnail_url': thumbnail_url,
                'audio_url': audio_url,
                'is_favorite': getattr(song, 'is_favorite', False),
                'keywords': keywords,
                'source_url': getattr(song, 'source_url', None),
                'created_at': getattr(song, 'created_at', datetime.utcnow()),
                'updated_at': getattr(song, 'updated_at', datetime.utcnow())
            })
        except Exception as e:
            print(f"Error in _convert_to_response: {e}")
            traceback.print_exc()
            return SongResponse.model_validate({
                'id': str(uuid.uuid4()),
                'title': 'Unknown Title',
                'artist': 'Unknown Artist',
                'album': None,
                'duration': 0,
                'thumbnail_url': None,
                'audio_url': None,
                'is_favorite': False,
                'keywords': None,
                'source_url': None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL format"""
        youtube_patterns = [
            r'(?:https?://)(?:www\.)?youtube\.com/watch\?v=[\w\-]{11}',
            r'(?:https?://)(?:www\.)?youtu\.be/[\w\-]{11}',
            r'(?:https?://)(?:www\.)?youtube\.com/embed/[\w\-]{11}',
            r'(?:https?://)(?:www\.)?youtube\.com/v/[\w\-]{11}',        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def _background_upload_to_cloudinary(self, song_id: str, audio_path: str, thumbnail_path: str, title: str):
        """Background task to upload files to Cloudinary and update database"""
        try:
            print(f"🚀 [Background] Starting Cloudinary upload for: {title}")
            print(f"🔍 [Background] Song ID: {song_id}")
            print(f"🔍 [Background] Audio path: {audio_path}")
            print(f"🔍 [Background] Thumbnail path: {thumbnail_path}")
            
            # Upload to Cloudinary
            cloudinary_result = self.cloudinary_service.upload_media_files(
                audio_path=audio_path,
                thumbnail_path=thumbnail_path,
                base_filename=title
            )
            
            print(f"🔍 [Background] Cloudinary result: {cloudinary_result}")
            
            if cloudinary_result.get('success'):
                # Prepare update data
                update_data = {}
                
                if cloudinary_result.get('audio') and cloudinary_result['audio'].get('success'):
                    update_data['audio_url_cloudinary'] = cloudinary_result['audio']['url']
                    print(f"✅ [Background] Audio uploaded to Cloudinary: {cloudinary_result['audio']['url']}")
                
                if cloudinary_result.get('thumbnail') and cloudinary_result['thumbnail'].get('success'):
                    update_data['thumbnail_url_cloudinary'] = cloudinary_result['thumbnail']['url']
                    print(f"✅ [Background] Thumbnail uploaded to Cloudinary: {cloudinary_result['thumbnail']['url']}")
                
                # Update database with Cloudinary URLs
                if update_data:
                    print(f"🔄 [Background] Preparing to update database with: {update_data}")
                    # Create new database session for background task
                    from app.config.database import SessionLocal
                    db = SessionLocal()
                    try:
                        song_repo = SongRepository(db)
                        updated_song = song_repo.update_song_cloudinary_urls(song_id, update_data)
                        if updated_song:
                            print(f"✅ [Background] Database updated successfully for song: {song_id}")
                        else:
                            print(f"❌ [Background] Failed to update database for song: {song_id}")
                        
                        # Clean up local files after successful upload
                        files_to_cleanup = []
                        if cloudinary_result.get('audio') and cloudinary_result['audio'].get('success'):
                            files_to_cleanup.append(audio_path)
                        if cloudinary_result.get('thumbnail') and cloudinary_result['thumbnail'].get('success') and thumbnail_path:
                            files_to_cleanup.append(thumbnail_path)
                        
                        if files_to_cleanup:
                            self.cloudinary_service.cleanup_local_files(files_to_cleanup)
                            print(f"🗑️ [Background] Local files cleaned up")
                        
                    finally:
                        db.close()
                else:
                    print(f"❌ [Background] No data to update for song: {song_id}")
                        
                print(f"✅ [Background] Cloudinary upload completed for: {title}")
            else:
                print(f"❌ [Background] Cloudinary upload failed: {cloudinary_result.get('message')}")
                
        except Exception as e:
            print(f"❌ [Background] Error in Cloudinary upload: {e}")
            import traceback
            traceback.print_exc()
    
    def download_from_youtube(self, request: YouTubeDownloadRequest, current_user = None) -> YouTubeDownloadResponse:
        """Download song from YouTube with new workflow"""
        try:
            # 1. Validation URL format
            if not self._is_valid_youtube_url(request.url):
                return YouTubeDownloadResponse(
                    success=False,
                    message='Invalid YouTube URL format'
                )
                
            # 2. Extract info để validate
            try:
                info = self.youtube_downloader.extract_info(request.url)
                if not info:
                    return YouTubeDownloadResponse(
                        success=False,
                        message='Video not found or unavailable'
                    )
            except Exception as e:
                error_msg = str(e)
                if "Video unavailable" in error_msg or "Private video" in error_msg:
                    return YouTubeDownloadResponse(
                        success=False,
                        message='Video is private, unavailable or restricted'
                    )
                elif "network" in error_msg.lower():
                    return YouTubeDownloadResponse(
                        success=False,
                        message='Network connection error. Please try again.'
                    )
                else:
                    return YouTubeDownloadResponse(
                        success=False,
                        message=f'Cannot access video: {error_msg}'
                    )
                    
            # 3. Check duration (max 2 hours)
            duration = info.get('duration', 0)
            if duration and duration > 7200:
                minutes = duration // 60
                hours = minutes // 60
                mins = minutes % 60
                return YouTubeDownloadResponse(
                    success=False,
                    message=f'Video too long ({hours}h {mins}m). Maximum 2 hours allowed.'
                )
            
            # 4. Check content type
            if info.get('is_live'):
                return YouTubeDownloadResponse(
                    success=False,
                    message='Cannot download live streams'
                )
            
            if duration and duration < 10:
                return YouTubeDownloadResponse(
                    success=False,
                    message='Video too short (minimum 10 seconds required)'
                )
              # Helper function for absolute URLs  
            def make_absolute_url(file_path):
                if not file_path:
                    return None
                if file_path.startswith('http'):
                    return file_path
                
                # Extract filename from full path
                filename = os.path.basename(file_path)
                base_url = settings.BASE_URL.rstrip('/')
                
                # Determine if it's audio or thumbnail based on path
                if 'audio' in file_path.lower():
                    return f"{base_url}/uploads/audio/{filename}"
                elif 'thumbnail' in file_path.lower():
                    return f"{base_url}/uploads/thumbnails/{filename}"
                else:
                    return None
              # Check if already exists - return Cloudinary URLs
            existing_song = self.song_repo.find_by_youtube_url(request.url)
            if existing_song:
                # For existing songs, prioritize Cloudinary URLs
                download_path = getattr(existing_song, 'audio_url_cloudinary', None)
                if not download_path:
                    download_path = make_absolute_url(getattr(existing_song, 'audio_local_path', None))
                
                return YouTubeDownloadResponse(
                    success=True,
                    message='Song already exists (from Cloudinary)',
                    song=self._convert_to_response(existing_song),
                    download_path=download_path
                )            # Download from YouTube
            success, audio_path, song_data, thumbnail_path = self.youtube_downloader.download_audio(request.url)
            
            if not success:
                return YouTubeDownloadResponse(
                    success=False,
                    message=audio_path  # audio_path contains error message when success=False
                )
            
            # Debug: Print song_data to see what we get from YouTube downloader
            print(f"🔍 [DEBUG] Song data from YouTube downloader: {song_data}")
            
            # Prepare song data with local paths (audio_path is the full path to downloaded file)
            song_data['audio_local_path'] = audio_path
            song_data['thumbnail_local_path'] = thumbnail_path
            
            print(f"🔍 [DEBUG] Song data before saving to DB: {song_data}")
            
            # Save to database with local paths
            user_id = current_user.id if current_user else None
            song = self.song_repo.create_song(song_data, user_id)
            
            print(f"🔍 [DEBUG] Song saved to DB: {song.__dict__}")
            
            # Return response immediately with local paths
            download_path = make_absolute_url(song_data.get('audio_local_path'))
            response = YouTubeDownloadResponse(
                success=True,
                message='Song downloaded successfully (uploading to cloud in background)',
                song=self._convert_to_response(song),
                download_path=download_path
            )
            
            # Start background upload to Cloudinary
            thread = threading.Thread(
                target=self._background_upload_to_cloudinary,
                args=(song.id, audio_path, thumbnail_path, song_data.get('title', 'unknown'))
            )
            thread.daemon = True
            thread.start()
            
            return response
            
        except Exception as e:
            print(f"Error in download_from_youtube: {e}")
            traceback.print_exc()
            return YouTubeDownloadResponse(
                success=False,
                message=f'Download failed: {str(e)}'
            )
