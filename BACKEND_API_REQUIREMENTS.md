# FastAPI Backend Requirements - Music Download System

## 📋 Tổng quan

Document này mô tả các FastAPI endpoints đơn giản mà Backend cần implement để hỗ trợ hệ thống download nhạc mới. Tập trung vào tính đơn giản và dễ implement.

---

## 🎯 Mục tiêu chính

- **Simple API Architecture**: APIs đơn giản, dễ hiểu
- **Basic Download Support**: Hỗ trợ chunked download cho files lớn (>5MB)
- **Essential Data Only**: Chỉ trả về thông tin cần thiết
- **FastAPI Best Practices**: Sử dụng FastAPI patterns

---

## 🔍 API 1: Music Search

### **FastAPI Endpoint:**
```python
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Song(BaseModel):
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: int  # seconds
    duration_formatted: str  # "3:45"
    thumbnail_url: str
    available: bool  # Ready for download?
    source: str  # "youtube"
    keywords: List[str] = []

class SearchResponse(BaseModel):
    success: bool = True
    songs: List[Song]
    total: int

@app.get("/api/songs/search", response_model=SearchResponse)
async def search_songs(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search for songs by title, artist, or keywords"""
    # Your search logic here
    songs = await search_music(q, limit, offset)
    total = await count_search_results(q)
    
    return SearchResponse(
        songs=songs,
        total=total
    )
```

#### **Example Response:**
```json
{
  "success": true,
  "songs": [
    {
      "id": "song_12345",
      "title": "Shape of You",
      "artist": "Ed Sheeran",
      "album": "÷ (Divide)",
      "duration": 263,
      "duration_formatted": "4:23",
      "thumbnail_url": "https://your-server.com/thumbnails/song_12345.jpg",
      "available": true,
      "source": "youtube",
      "keywords": ["pop", "chart", "acoustic"]
    }
  ],
  "total": 150
}
```

---

## ⚡ API 2: Download Information

### **FastAPI Endpoint:**
```python
class FileInfo(BaseModel):
    size: int  # File size in bytes
    chunks: int  # Number of chunks (for files > 5MB)
    chunk_size: int = 1048576  # 1MB chunks
    checksum: str  # Simple MD5 hash

class DownloadInfo(BaseModel):
    song_id: str
    ready: bool
    processing: bool = False
    error: Optional[str] = None
    
    # Only if ready = True
    audio_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_info: Optional[FileInfo] = None

@app.get("/api/songs/{song_id}/download-info", response_model=DownloadInfo)
async def get_download_info(song_id: str):
    """Get download information for a song"""
    song = await get_song_by_id(song_id)
    
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    if song.is_processing:
        return DownloadInfo(
            song_id=song_id,
            ready=False,
            processing=True
        )
    
    if not song.is_ready:
        return DownloadInfo(
            song_id=song_id,
            ready=False,
            error="Song processing failed"
        )
    
    # Calculate file info
    file_size = await get_file_size(song.audio_file_path)
    chunks_needed = (file_size // 1048576) + (1 if file_size % 1048576 else 0)
    
    return DownloadInfo(
        song_id=song_id,
        ready=True,
        audio_url=f"/api/songs/{song_id}/download",
        thumbnail_url=f"/api/songs/{song_id}/thumbnail",
        file_info=FileInfo(
            size=file_size,
            chunks=chunks_needed if file_size > 5 * 1024 * 1024 else 1,
            checksum=await calculate_md5(song.audio_file_path)
        )
    )
```

#### **Example Response (Ready):**
```json
{
  "song_id": "song_12345",
  "ready": true,
  "processing": false,
  "audio_url": "/api/songs/song_12345/download",
  "thumbnail_url": "/api/songs/song_12345/thumbnail",
  "file_info": {
    "size": 5242880,
    "chunks": 5,
    "chunk_size": 1048576,
    "checksum": "a1b2c3d4e5f6..."
  }
}
```

#### **Example Response (Processing):**
```json
{
  "song_id": "song_12345",
  "ready": false,
  "processing": true
}
```

---

## 📦 API 3: File Download

### **FastAPI Endpoints:**

#### **3.1 Full File Download (for files < 5MB):**
```python
from fastapi import Response
from fastapi.responses import FileResponse

@app.get("/api/songs/{song_id}/download")
async def download_song(song_id: str):
    """Download complete audio file"""
    song = await get_song_by_id(song_id)
    
    if not song or not song.is_ready:
        raise HTTPException(status_code=404, detail="Song not available")
    
    return FileResponse(
        path=song.audio_file_path,
        media_type="audio/mpeg",
        filename=f"{song.title} - {song.artist}.mp3"
    )

@app.get("/api/songs/{song_id}/thumbnail")
async def download_thumbnail(song_id: str):
    """Download thumbnail image"""
    song = await get_song_by_id(song_id)
    
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    return FileResponse(
        path=song.thumbnail_path,
        media_type="image/jpeg"
    )
```

#### **3.2 Chunked Download (for files > 5MB):**
```python
from fastapi import Header, HTTPException
import os

@app.get("/api/songs/{song_id}/download/chunk/{chunk_index}")
async def download_chunk(
    song_id: str, 
    chunk_index: int,
    range: Optional[str] = Header(None)
):
    """Download specific chunk of audio file"""
    song = await get_song_by_id(song_id)
    
    if not song or not song.is_ready:
        raise HTTPException(status_code=404, detail="Song not available")
    
    file_path = song.audio_file_path
    file_size = os.path.getsize(file_path)
    chunk_size = 1048576  # 1MB
    
    start = chunk_index * chunk_size
    end = min(start + chunk_size - 1, file_size - 1)
    
    if start >= file_size:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    # Read chunk data
    with open(file_path, "rb") as f:
        f.seek(start)
        chunk_data = f.read(end - start + 1)
    
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(chunk_data))
    }
    
    return Response(
        content=chunk_data,
        status_code=206,  # Partial Content
        headers=headers,
        media_type="audio/mpeg"
    )
```

---

## 🔄 API 4: Request Processing

### **FastAPI Endpoint:**
```python
class ProcessRequest(BaseModel):
    song_url: str  # YouTube URL or other source
    quality: str = "medium"  # low, medium, high

class ProcessResponse(BaseModel):
    success: bool
    message: str
    song_id: Optional[str] = None
    status: str  # "queued", "processing", "completed", "failed"

@app.post("/api/songs/process", response_model=ProcessResponse)
async def process_song(request: ProcessRequest):
    """Request song processing from external source"""
    try:
        # Create new song entry
        song_id = await create_song_entry(request.song_url)
        
        # Add to processing queue
        await add_to_processing_queue(song_id, request.song_url, request.quality)
        
        return ProcessResponse(
            success=True,
            message="Song added to processing queue",
            song_id=song_id,
            status="queued"
        )
        
    except Exception as e:
        return ProcessResponse(
            success=False,
            message=f"Failed to process song: {str(e)}",
            status="failed"
        )
```

#### **Example Request:**
```json
{
  "song_url": "https://youtube.com/watch?v=JGwWNGJdvx8",
  "quality": "medium"
}
```

#### **Example Response:**
```json
{
  "success": true,
  "message": "Song added to processing queue",
  "song_id": "song_12345",
  "status": "queued"
}
```

---

## 📊 API 5: Simple Analytics (Optional)

### **FastAPI Endpoint:**
```python
class DownloadEvent(BaseModel):
    song_id: str
    event_type: str  # "started", "completed", "failed"
    error_message: Optional[str] = None

@app.post("/api/analytics/download")
async def track_download(event: DownloadEvent):
    """Track download events for analytics"""
    await log_download_event(
        song_id=event.song_id,
        event_type=event.event_type,
        error_message=event.error_message,
        timestamp=datetime.utcnow()
    )
    
    return {"success": True, "message": "Event logged"}
```

---

## 🗄️ Database Models

### **SQLAlchemy Models:**
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Song(Base):
    __tablename__ = "songs"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    album = Column(String, nullable=True)
    duration = Column(Integer, nullable=False)  # seconds
    duration_formatted = Column(String, nullable=False)
    
    # Source info
    source = Column(String, nullable=False)  # "youtube"
    source_url = Column(String, nullable=False)
    
    # Processing status
    is_ready = Column(Boolean, default=False)
    is_processing = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # File paths (local storage)
    audio_file_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    
    # Metadata
    keywords = Column(Text, nullable=True)  # JSON array as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DownloadLog(Base):
    __tablename__ = "download_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    song_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🛠️ Helper Functions

### **Core Functions:**
```python
import hashlib
import aiofiles
from typing import List

async def search_music(query: str, limit: int, offset: int) -> List[Song]:
    """Search songs in database"""
    # Your database query logic
    pass

async def get_song_by_id(song_id: str) -> Optional[Song]:
    """Get song by ID"""
    # Your database query logic
    pass

async def calculate_md5(file_path: str) -> str:
    """Calculate MD5 hash of file"""
    hash_md5 = hashlib.md5()
    async with aiofiles.open(file_path, "rb") as f:
        async for chunk in f:
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

async def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(file_path)

async def add_to_processing_queue(song_id: str, url: str, quality: str):
    """Add song to background processing queue"""
    # Your queue logic (Celery, RQ, etc.)
    pass
```

---

## ⚙️ FastAPI Configuration

### **Main Application:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="TxtMusic API",
    description="Simple music download API",
    version="2.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all endpoints above...

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### **Requirements.txt:**
```txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==1.4.41
aiofiles==22.1.0
python-multipart==0.0.6
pydantic==1.10.8
```

---

## 🚀 Simple Deployment

### **Docker Setup:**
```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Run Commands:**
```bash
# Development
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📁 File Storage Strategy

### **Simple Local Storage:**
```python
import os
from pathlib import Path

# File structure
STORAGE_ROOT = "/app/storage"
AUDIO_DIR = f"{STORAGE_ROOT}/audio"
THUMBNAIL_DIR = f"{STORAGE_ROOT}/thumbnails"

def get_audio_path(song_id: str) -> str:
    return f"{AUDIO_DIR}/{song_id}.mp3"

def get_thumbnail_path(song_id: str) -> str:
    return f"{THUMBNAIL_DIR}/{song_id}.jpg"

# Ensure directories exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
```

---

## 🧪 Testing Examples

### **Test with curl:**
```bash
# Search songs
curl "http://localhost:8000/api/songs/search?q=shape+of+you"

# Get download info
curl "http://localhost:8000/api/songs/song_12345/download-info"

# Download full file
curl -o song.mp3 "http://localhost:8000/api/songs/song_12345/download"

# Download chunk
curl -H "Range: bytes=0-1048575" \
     "http://localhost:8000/api/songs/song_12345/download/chunk/0"

# Request processing
curl -X POST "http://localhost:8000/api/songs/process" \
     -H "Content-Type: application/json" \
     -d '{"song_url": "https://youtube.com/watch?v=test", "quality": "medium"}'
```

---

## 🔧 Error Handling

### **Simple Error Responses:**
```python
from fastapi import HTTPException

# Standard error format
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# Usage in endpoints
@app.get("/api/songs/{song_id}")
async def get_song(song_id: str):
    song = await get_song_by_id(song_id)
    if not song:
        raise HTTPException(
            status_code=404, 
            detail="Song not found"
        )
    return song
```

---

## 📋 Implementation Checklist

### **Phase 1: Basic APIs**
- [ ] Setup FastAPI project
- [ ] Implement search endpoint
- [ ] Implement download-info endpoint
- [ ] Setup database models

### **Phase 2: File Handling**
- [ ] Implement file download endpoint
- [ ] Add chunked download support
- [ ] Setup file storage system
- [ ] Add thumbnail support

### **Phase 3: Processing**
- [ ] Implement processing request endpoint
- [ ] Setup background task queue
- [ ] Add YouTube download logic
- [ ] Implement processing status tracking

### **Phase 4: Polish**
- [ ] Add basic analytics
- [ ] Improve error handling
- [ ] Add request validation
- [ ] Write documentation

---

**🎵 Kết quả: Một FastAPI backend đơn giản, dễ hiểu và dễ implement để hỗ trợ music download system!**
