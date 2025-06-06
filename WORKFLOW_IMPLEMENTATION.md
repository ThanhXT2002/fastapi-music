# New Workflow Implementation Summary

## 🔄 **New Download Workflow**

### **Model Updates**
Đã cập nhật Song model với 4 fields mới để tách biệt local và Cloudinary URLs:

```python
class Song(Base):
    # ...existing fields...
    
    # Cloudinary URLs (for production serving)
    thumbnail_url_cloudinary = Column(String(500), nullable=True)  
    audio_url_cloudinary = Column(String(500), nullable=True)
    
    # Local paths (for immediate serving)
    thumbnail_local_path = Column(String(500), nullable=True)  
    audio_local_path = Column(String(500), nullable=True)
```

### **Workflow Logic**

#### 1. **New Download Request**
```
1. Download YouTube video → Local files
2. Save to database với local paths
3. Return response ngay với local URLs (fast response)
4. Background: Upload to Cloudinary 
5. Background: Update database với Cloudinary URLs
6. Background: Cleanup local files
```

#### 2. **Existing Song Request**
```
1. Check database for existing song
2. Return Cloudinary URLs (optimized & reliable)
```

### **Code Changes**

#### **SongController** (`app/api/controllers/song.py`)
- `_convert_to_response()`: Prioritize Cloudinary URLs over local paths
- `download_from_youtube()`: New workflow implementation
- `_background_upload_to_cloudinary()`: Background task for Cloudinary upload

#### **SongRepository** (`app/internal/storage/repositories/song.py`)
- `update_song_cloudinary_urls()`: New method to update Cloudinary URLs in background

#### **YouTubeDownloader** (`app/internal/utils/youtube_downloader.py`)
- `_extract_song_data()`: Updated to use new field names

### **Benefits**

#### ⚡ **Fast Response**
- User gets immediate response với local files
- No waiting for Cloudinary upload

#### 🔄 **Background Processing**
- Cloudinary upload runs in background thread
- User experience không bị ảnh hưởng

#### 📈 **Scalability**
- Existing songs serve from Cloudinary (CDN)
- New songs serve locally first, then migrate to CDN

#### 🛡️ **Reliability**
- Fallback mechanism: local → Cloudinary
- Error handling cho background tasks

### **Database Schema**
```sql
-- New columns added to songs table
ALTER TABLE songs ADD COLUMN thumbnail_url_cloudinary VARCHAR(500);
ALTER TABLE songs ADD COLUMN audio_url_cloudinary VARCHAR(500);
ALTER TABLE songs ADD COLUMN thumbnail_local_path VARCHAR(500);
ALTER TABLE songs ADD COLUMN audio_local_path VARCHAR(500);
```

### **API Response Examples**

#### **New Download (Local URLs)**
```json
{
  "success": true,
  "message": "Song downloaded successfully (uploading to cloud in background)",
  "song": {
    "thumbnail_url": "http://localhost:8000/uploads/thumbnails/abc123.jpg",
    "audio_url": "http://localhost:8000/uploads/audio/abc123.mp3"
  },
  "download_path": "http://localhost:8000/uploads/audio/abc123.mp3"
}
```

#### **Existing Song (Cloudinary URLs)**
```json
{
  "success": true,
  "message": "Song already exists (from Cloudinary)",
  "song": {
    "thumbnail_url": "https://res.cloudinary.com/xxx/image/upload/xxx.jpg",
    "audio_url": "https://res.cloudinary.com/xxx/video/upload/xxx.mp3"
  },
  "download_path": "https://res.cloudinary.com/xxx/video/upload/xxx.mp3"
}
```

### **Background Process Flow**
```
1. 🚀 Start Cloudinary upload
2. 📤 Upload audio file
3. 📤 Upload thumbnail file  
4. 💾 Update database với Cloudinary URLs
5. 🗑️ Clean up local files
6. ✅ Log completion
```

### **Error Handling**
- Background task failures không affect user experience
- Local files kept as fallback if Cloudinary fails
- Database rollback on update errors
- Detailed logging for debugging

### **Testing**
```bash
# Test new download
curl -X POST "http://localhost:8000/api/v1/songs/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Test existing song
curl -X POST "http://localhost:8000/api/v1/songs/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### **Monitoring**
Check console logs for background processes:
```
🚀 [Background] Starting Cloudinary upload for: Song Title
✅ [Background] Audio uploaded to Cloudinary: https://...
✅ [Background] Database updated for song: abc-123
🗑️ [Background] Local files cleaned up
```
