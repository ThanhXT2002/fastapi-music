import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from app.internal.utils.youtube_downloader import YouTubeDownloader
from app.api.v2.models.song import SongV2
from app.api.v2.helpers import format_duration, get_audio_path, get_thumbnail_path
from app.config.database import get_db


class YouTubeServiceV2:
    def __init__(self):
        self.downloader = YouTubeDownloader()
    
    async def extract_video_info(self, url: str) -> Optional[Dict]:
        """Extract video information from YouTube URL"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self.downloader.extract_info, url)
            
            if not info:
                return None
                
            return {
                'video_id': info.get('id', ''),
                'title': info.get('title', 'Unknown Title'),
                'artist': info.get('uploader', 'Unknown Artist'),
                'duration': info.get('duration', 0),
                'thumbnail_url': info.get('thumbnail', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
            }
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return None
    
    async def create_song_from_url(self, url: str, quality: str = "medium") -> Optional[str]:
        """Create song entry from YouTube URL"""
        db = next(get_db())
        try:
            # Extract video info
            video_info = await self.extract_video_info(url)
            if not video_info:
                raise Exception("Could not extract video information")
            
            # Generate song ID
            song_id = str(uuid.uuid4())
            
            # Create song entry with extracted info
            duration = video_info.get('duration', 0)
            keywords = self._extract_keywords(video_info)
            
            song = SongV2(
                id=song_id,
                title=video_info['title'],
                artist=video_info['artist'],
                album=None,
                duration=duration,
                duration_formatted=format_duration(duration),
                source="youtube",
                source_url=url,
                is_ready=False,
                is_processing=True,
                keywords=json.dumps(keywords)
            )
            
            db.add(song)
            db.commit()
            
            # Start background download
            asyncio.create_task(self._download_song_background(song_id, url, video_info, quality))
            
            return song_id
            
        except Exception as e:
            db.rollback()
            print(f"Error creating song from URL: {e}")
            return None
        finally:
            db.close()
    
    def _extract_keywords(self, video_info: Dict) -> List[str]:
        """Extract keywords from video info"""
        keywords = []
        
        # Add basic keywords based on title and description
        title = video_info.get('title', '').lower()
        description = video_info.get('description', '').lower()
        
        # Common music keywords
        music_keywords = ['music', 'song', 'audio', 'mp3', 'official', 'video', 'live', 'cover', 'remix']
        
        for keyword in music_keywords:
            if keyword in title or keyword in description:
                keywords.append(keyword)
        
        # Add duration-based keywords
        duration = video_info.get('duration', 0)
        if duration:
            if duration < 180:  # < 3 minutes
                keywords.append('short')
            elif duration > 600:  # > 10 minutes
                keywords.append('long')
            else:
                keywords.append('medium')
        
        return keywords[:10]  # Limit to 10 keywords
    
    async def _download_song_background(self, song_id: str, url: str, video_info: Dict, quality: str):
        """Background task to download song"""
        db = next(get_db())
        try:
            print(f"Starting download for song {song_id}")
            
            # Download audio
            loop = asyncio.get_event_loop()
            download_result = await loop.run_in_executor(
                None, 
                self.downloader.download_audio_to_server, 
                url, 
                video_info['video_id']
            )
            
            if not download_result.get('success'):
                raise Exception(download_result.get('message', 'Download failed'))
            
            # Download thumbnail
            thumbnail_result = await self._download_thumbnail(song_id, video_info.get('thumbnail_url'))
              # Update song record with actual paths
            song = db.query(SongV2).filter(SongV2.id == song_id).first()
            if song:
                song.is_processing = False
                song.is_ready = True
                
                # Get the correct file paths from download result
                video_data = download_result.get('video_data', {})
                local_file_path = video_data.get('local_file_path', '')
                
                if local_file_path and os.path.exists(local_file_path):
                    song.audio_file_path = local_file_path
                else:
                    # Fallback to constructing path
                    song.audio_file_path = get_audio_path(song_id)
                
                song.thumbnail_path = thumbnail_result.get('local_thumbnail_path') if thumbnail_result.get('success') else None
                song.updated_at = datetime.utcnow()
                
                db.commit()
                print(f"Song {song_id} download completed successfully")
                print(f"Audio file path: {song.audio_file_path}")
            
        except Exception as e:
            print(f"Error downloading song {song_id}: {e}")
            
            # Update song with error
            song = db.query(SongV2).filter(SongV2.id == song_id).first()
            if song:
                song.is_processing = False
                song.is_ready = False
                song.processing_error = str(e)
                song.updated_at = datetime.utcnow()
                db.commit()
                
        finally:
            db.close()
    
    async def _download_thumbnail(self, song_id: str, thumbnail_url: str) -> Dict:
        """Download thumbnail image"""
        try:
            if not thumbnail_url:
                return {"success": False, "message": "No thumbnail URL"}
            
            import requests
            
            # Use requests for sync download in executor
            loop = asyncio.get_event_loop()
            
            def download_sync():
                try:
                    response = requests.get(thumbnail_url, timeout=30)
                    if response.status_code == 200:
                        thumbnail_path = get_thumbnail_path(song_id)
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                        
                        # Save thumbnail
                        with open(thumbnail_path, 'wb') as f:
                            f.write(response.content)
                        
                        return {
                            "success": True, 
                            "local_thumbnail_path": thumbnail_path
                        }
                    return {"success": False, "message": "Failed to download thumbnail"}
                except Exception as e:
                    return {"success": False, "message": str(e)}
            
            return await loop.run_in_executor(None, download_sync)
            
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_download_progress(self, song_id: str) -> Dict:
        """Get download progress for a song"""
        db = next(get_db())
        try:
            song = db.query(SongV2).filter(SongV2.id == song_id).first()
            
            if not song:
                return {"error": "Song not found"}
            
            if song.is_ready:
                return {
                    "status": "completed",
                    "progress": 100,
                    "message": "Download completed"
                }
            elif song.is_processing:
                return {
                    "status": "processing", 
                    "progress": 50,  # Could implement real progress tracking
                    "message": "Downloading audio..."
                }
            elif song.processing_error:
                return {
                    "status": "failed",
                    "progress": 0,
                    "message": song.processing_error
                }
            else:
                return {
                    "status": "queued",
                    "progress": 0,
                    "message": "Waiting to start"
                }
                
        finally:
            db.close()
    
    async def retry_failed_download(self, song_id: str) -> bool:
        """Retry downloading a failed song"""
        db = next(get_db())
        try:
            song = db.query(SongV2).filter(SongV2.id == song_id).first()
            
            if not song:
                return False
            
            if song.is_processing or song.is_ready:
                return False  # Already processing or done
            
            # Reset status and retry
            song.is_processing = True
            song.processing_error = None
            song.updated_at = datetime.utcnow()
            db.commit()
            
            # Extract video info again
            video_info = await self.extract_video_info(song.source_url)
            if not video_info:
                song.processing_error = "Could not extract video info on retry"
                song.is_processing = False
                db.commit()
                return False
            
            # Start download again
            asyncio.create_task(self._download_song_background(song_id, song.source_url, video_info, "medium"))
            
            return True
            
        except Exception as e:
            print(f"Error retrying download: {e}")
            return False
        finally:
            db.close()
