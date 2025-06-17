import hashlib
import aiofiles
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.config.database import get_db
from app.api.v2.models.song import SongV2, DownloadLogV2
from app.api.v2.schemas.song import Song as SongSchema


async def search_music(query: str, limit: int, offset: int, db: Session = None) -> List[SongSchema]:
    """Search songs in database"""
    if db is None:
        db = next(get_db())
    
    try:
        # Search by title, artist, or keywords
        search_filter = or_(
            SongV2.title.ilike(f"%{query}%"),
            SongV2.artist.ilike(f"%{query}%"),
            SongV2.album.ilike(f"%{query}%"),
            SongV2.keywords.ilike(f"%{query}%")
        )
        
        songs = db.query(SongV2).filter(search_filter).offset(offset).limit(limit).all()
        
        result = []
        for song in songs:
            # Parse keywords from JSON string
            keywords = []
            if song.keywords:
                try:
                    keywords = json.loads(song.keywords)
                except:
                    keywords = []
            
            result.append(SongSchema(
                id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                duration=song.duration,
                duration_formatted=song.duration_formatted,
                thumbnail_url=f"/api/v2/songs/{song.id}/thumbnail" if song.thumbnail_path else "",
                available=song.is_ready,
                source=song.source,
                keywords=keywords
            ))
        
        return result
    finally:
        db.close()


async def count_search_results(query: str, db: Session = None) -> int:
    """Count search results"""
    if db is None:
        db = next(get_db())
    
    try:
        search_filter = or_(
            SongV2.title.ilike(f"%{query}%"),
            SongV2.artist.ilike(f"%{query}%"),
            SongV2.album.ilike(f"%{query}%"),
            SongV2.keywords.ilike(f"%{query}%")
        )
        
        count = db.query(func.count(SongV2.id)).filter(search_filter).scalar()
        return count or 0
    finally:
        db.close()


async def get_song_by_id(song_id: str, db: Session = None) -> Optional[SongV2]:
    """Get song by ID"""
    if db is None:
        db = next(get_db())
    
    try:
        return db.query(SongV2).filter(SongV2.id == song_id).first()
    finally:
        db.close()


async def create_song_entry(song_url: str, db: Session = None) -> str:
    """Create new song entry"""
    if db is None:
        db = next(get_db())
    
    try:
        song_id = str(uuid.uuid4())
        
        # Create basic song entry (will be populated during processing)
        song = SongV2(
            id=song_id,
            title="Processing...",
            artist="Unknown",
            duration=0,
            duration_formatted="0:00",
            source="youtube",
            source_url=song_url,
            is_processing=True
        )
        
        db.add(song)
        db.commit()
        
        return song_id
    finally:
        db.close()


async def calculate_md5(file_path: str) -> str:
    """Calculate MD5 hash of file"""
    hash_md5 = hashlib.md5()
    try:
        async with aiofiles.open(file_path, "rb") as f:
            async for chunk in f:
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return "unknown"


async def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


async def add_to_processing_queue(song_id: str, url: str, quality: str):
    """Add song to background processing queue"""
    # For now, we'll just mark it as queued
    # In a real implementation, you would add this to Celery, RQ, or another queue
    print(f"Added song {song_id} to processing queue: {url} (quality: {quality})")


async def log_download_event(song_id: str, event_type: str, error_message: Optional[str] = None, db: Session = None):
    """Log download event for analytics"""
    if db is None:
        db = next(get_db())
    
    try:
        log_entry = DownloadLogV2(
            song_id=song_id,
            event_type=event_type,
            error_message=error_message
        )
        
        db.add(log_entry)
        db.commit()
    finally:
        db.close()


def format_duration(seconds: int) -> str:
    """Format duration from seconds to MM:SS format"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def get_audio_path(song_id: str) -> str:
    """Get audio file path"""
    from app.config.config import settings
    return os.path.join(settings.AUDIO_DIRECTORY, f"{song_id}.mp3")


def get_thumbnail_path(song_id: str) -> str:
    """Get thumbnail file path"""
    from app.config.config import settings
    return os.path.join(settings.THUMBNAIL_DIRECTORY, f"{song_id}.jpg")
