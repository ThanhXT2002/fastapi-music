from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import re  
import json
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
            # Parse JSON fields if they exist
            keywords = song.keywords
            if isinstance(keywords, str):
                try:
                    keywords_list = json.loads(keywords)
                    keywords = json.dumps(keywords_list)  # Keep as JSON string for response
                except:
                    keywords = json.dumps([keywords]) if keywords else None
            
            # Helper function to convert relative URLs to absolute URLs
            def make_absolute_url(url):
                if not url:
                    return url
                if url.startswith('http'):
                    return url  # Already absolute
                base_url = settings.BASE_URL.rstrip('/')
                return f"{base_url}{url}" if url.startswith('/') else f"{base_url}/{url}"
            
            return SongResponse(
                id=getattr(song, 'id', str(uuid.uuid4())),
                title=getattr(song, 'title', 'Unknown Title'),
                artist=getattr(song, 'artist', 'Unknown Artist'),
                album=getattr(song, 'album', None),
                duration=getattr(song, 'duration', 0),
                thumbnail_url=make_absolute_url(getattr(song, 'thumbnail_url', None)),
                audio_url=make_absolute_url(getattr(song, 'audio_url', None)),
                local_path=getattr(song, 'local_path', None),
                is_favorite=getattr(song, 'is_favorite', False),
                keywords=keywords,
                source_url=getattr(song, 'source_url', None),
                created_at=getattr(song, 'created_at', datetime.utcnow()),
                updated_at=getattr(song, 'updated_at', datetime.utcnow())
            )
        except Exception as e:
            print(f"Error in _convert_to_response: {e}")
            return SongResponse(
                id=str(uuid.uuid4()),
                title='Unknown Title',
                artist='Unknown Artist',
                album=None,
                duration=0,
                thumbnail_url=None,
                audio_url=None,
                local_path=None,
                is_favorite=False,
                keywords=None,
                source_url=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL format"""
        # Các pattern phổ biến cho YouTube URLs
        youtube_patterns = [
            r'(?:https?://)(?:www\.)?youtube\.com/watch\?v=[\w\-]{11}',  # youtube.com/watch?v=ID
            r'(?:https?://)(?:www\.)?youtu\.be/[\w\-]{11}',             # youtu.be/ID
            r'(?:https?://)(?:www\.)?youtube\.com/embed/[\w\-]{11}',    # youtube.com/embed/ID
            r'(?:https?://)(?:www\.)?youtube\.com/v/[\w\-]{11}',        # youtube.com/v/ID
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def download_from_youtube(self, request: YouTubeDownloadRequest, current_user = None) -> YouTubeDownloadResponse:
        """Download song from YouTube"""
        from app.config.config import settings
        
        try:
            # 1. VALIDATION URL FORMAT TRƯỚC TIÊN
            if not self._is_valid_youtube_url(request.url):
                return YouTubeDownloadResponse(
                    success=False,
                    message='Invalid YouTube URL format'
                )
                
            # 2. EXTRACT INFO ĐỂ VALIDATE (không download)
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
                    
            # 3. KIỂM TRA DURATION (MAX 2 TIẾNG = 7200 SECONDS)
            duration = info.get('duration', 0)
            if duration and duration > 7200:  # 2 hours
                minutes = duration // 60
                hours = minutes // 60
                mins = minutes % 60
                return YouTubeDownloadResponse(
                    success=False,
                    message=f'Video too long ({hours}h {mins}m). Maximum 2 hours allowed.'
                )
            
            # 4. KIỂM TRA LOẠI CONTENT (tránh livestream, shorts quá ngắn)
            if info.get('is_live'):
                return YouTubeDownloadResponse(
                    success=False,
                    message='Cannot download live streams'
                )
            
            if duration and duration < 10:  # Tránh video quá ngắn (< 10 giây)
                return YouTubeDownloadResponse(
                    success=False,
                    message='Video too short (minimum 10 seconds required)'
                )
                
            
            # Helper function to convert relative URLs to absolute URLs
            def make_absolute_url(url):
                if not url:
                    return url
                if url.startswith('http'):
                    return url  # Already absolute
                base_url = settings.BASE_URL.rstrip('/')
                return f"{base_url}{url}" if url.startswith('/') else f"{base_url}/{url}"
            
            # Check if already downloaded
            existing_song = self.song_repo.find_by_youtube_url(request.url)
            if existing_song:
                # Convert local_path or audio_url to absolute URL for download_path
                download_path = make_absolute_url(getattr(existing_song, 'audio_url', None))
                if not download_path and hasattr(existing_song, 'local_path'):                    # If no audio_url, construct from local_path
                    import os
                    filename = os.path.basename(existing_song.local_path) if existing_song.local_path else None
                    if filename:
                        download_path = f"{settings.BASE_URL.rstrip('/')}/uploads/audio/{filename}"
                
                return YouTubeDownloadResponse(
                    success=True,
                    message='Song already downloaded',
                    song=self._convert_to_response(existing_song),
                    download_path=download_path
                )
              # Download from YouTube
            success, result, song_data, thumbnail_path = self.youtube_downloader.download_audio(request.url)
            
            if not success:
                return YouTubeDownloadResponse(
                    success=False,
                    message=result
                )
            
            # Upload to Cloudinary
            try:
                print(f"🚀 Starting Cloudinary upload for: {song_data.get('title')}")
                print(f"   Audio path: {song_data.get('local_path')}")
                print(f"   Thumbnail path: {thumbnail_path}")
                
                cloudinary_result = self.cloudinary_service.upload_media_files(
                    audio_path=song_data.get('local_path'),
                    thumbnail_path=thumbnail_path,
                    base_filename=song_data.get('title', 'unknown')
                )
                
                print(f"📊 Cloudinary result: {cloudinary_result}")
                
                if cloudinary_result.get('success'):
                    # Update song_data with Cloudinary URLs (reuse existing fields)
                    if cloudinary_result.get('audio') and cloudinary_result['audio'].get('success'):
                        song_data['audio_url'] = cloudinary_result['audio']['url']
                        print(f"✅ Audio uploaded to Cloudinary: {cloudinary_result['audio']['url']}")
                    
                    if cloudinary_result.get('thumbnail') and cloudinary_result['thumbnail'].get('success'):
                        song_data['thumbnail_url'] = cloudinary_result['thumbnail']['url']
                        print(f"✅ Thumbnail uploaded to Cloudinary: {cloudinary_result['thumbnail']['url']}")
                    else:
                        print(f"⚠️ Thumbnail not uploaded to Cloudinary, keeping local file")
                    
                    # Clean up local files after successful upload
                    files_to_cleanup = []
                    if cloudinary_result.get('audio') and cloudinary_result['audio'].get('success'):
                        files_to_cleanup.append(song_data.get('local_path'))
                    
                    # If we have a thumbnail path from earlier, we can use it for cleanup
                    if cloudinary_result.get('thumbnail') and cloudinary_result['thumbnail'].get('success') and thumbnail_path:
                        files_to_cleanup.append(thumbnail_path)
                    
                    if files_to_cleanup:
                        self.cloudinary_service.cleanup_local_files(files_to_cleanup)
                    
                    print(f"✅ Cloudinary upload completed for: {song_data.get('title')}")
                    print(f"   Message: {cloudinary_result.get('message', 'Upload completed')}")
                else:
                    print(f"⚠️ Cloudinary upload failed, keeping local files: {cloudinary_result.get('message')}")
                    # Keep local URLs as fallback
                    
            except Exception as cloudinary_error:
                print(f"❌ Cloudinary upload error: {cloudinary_error}")
                import traceback
                traceback.print_exc()
                # Continue with local files as fallback            # Save to database
            user_id = current_user.id if current_user else None
            song = self.song_repo.create_song(song_data, user_id)
            
            # Get download path (prioritize Cloudinary URL)
            download_path = song_data.get('audio_url') or make_absolute_url(result)
              # Create response with complete information
            return YouTubeDownloadResponse(
                success=True,
                message='Song downloaded and uploaded to cloud successfully',
                song=self._convert_to_response(song),
                download_path=download_path
            )
            
        except Exception as e:
            print(f"Error in download_from_youtube: {e}")
            return YouTubeDownloadResponse(
                success=False,
                message=f'Download failed: {str(e)}'
            )
