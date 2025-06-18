# FastAPI Music V3 Documentation

## Tổng quan

FastAPI Music V3 được thiết kế theo logic đơn giản và hiệu quả:

1. **Get Info**: Lấy thông tin bài hát nhanh từ YouTube
2. **Background Processing**: Tải file audio và thumbnail trong background  
3. **Status Polling**: Theo dõi tiến trình xử lý
4. **Chunk Download**: Tải file với streaming chunks

## API Endpoints

### Base URL: `/api/v3`

### 1. Health Check
```
GET /health
```

**Response:**
```json
{
  "success": true,
  "message": "FastAPI Music V3 is running",
  "version": "3.0.0"
}
```

### 2. Get Song Info
```
POST /songs/info
```

**Request Body:**
```json
{
  "youtube_url": "https://youtu.be/dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "success": true,
  "message": "get info video success",
  "data": {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "artist": "RickAstleyVEVO",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    "duration": 212,
    "duration_formatted": "03:32",
    "keywords": ["Music", "Pop"],
    "original_url": "https://youtu.be/dQw4w9WgXcQ",
    "created_at": "2025-06-17T14:46:57"
  }
}
```

**Features:**
- ✅ Trả về thông tin ngay lập tức
- ✅ Thumbnail URL gốc từ YouTube (không cần tải về)
- ✅ Bắt đầu background processing tự động
- ✅ Xử lý duplicate URLs

### 3. Check Status
```
GET /songs/status/{song_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Status retrieved successfully",
  "data": {
    "id": "dQw4w9WgXcQ",
    "status": "completed",
    "progress": 1.0,
    "error_message": null,
    "audio_filename": "dQw4w9WgXcQ_1750161805.m4a",
    "thumbnail_filename": "dQw4w9WgXcQ_1750161805.jpg",
    "updated_at": "2025-06-17T14:47:25"
  }
}
```

**Status Values:**
- `pending`: Đang chờ xử lý
- `processing`: Đang tải file
- `completed`: Hoàn thành
- `failed`: Thất bại

**Progress Values:**
- `0.0`: Chưa bắt đầu
- `0.5`: Đang xử lý
- `1.0`: Hoàn thành

### 4. Download Audio
```
GET /songs/download/{song_id}
```

**Response:**
- **Content-Type**: `audio/mpeg`
- **Content-Disposition**: `attachment; filename="Song Title.m4a"`
- **Content-Length**: File size in bytes
- **Accept-Ranges**: `bytes`

**Features:**
- ✅ Streaming download với chunks
- ✅ Không cần kiểm tra logic phức tạp
- ✅ Resume support
- ✅ Filename tự động

### 5. Get Thumbnail (Optional)
```
GET /songs/thumbnail/{song_id}
```

**Response:**
- **Content-Type**: `image/jpeg`, `image/png`, or `image/webp`
- Streaming image data

**Note**: Có thể dùng `thumbnail_url` từ response của `/songs/info` thay vì endpoint này.

## Workflow Frontend

### 1. Lấy thông tin bài hát
```javascript
const response = await fetch('/api/v3/songs/info', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ youtube_url: url })
});

const result = await response.json();
const songInfo = result.data;

// Hiển thị thông tin ngay lập tức
displaySongInfo(songInfo);
```

### 2. Polling status
```javascript
const pollStatus = async (songId) => {
  const response = await fetch(`/api/v3/songs/status/${songId}`);
  const result = await response.json();
  const status = result.data;
  
  updateProgressBar(status.progress);
  
  if (status.status === 'completed') {
    enableDownloadButton(songId);
  } else if (status.status === 'failed') {
    showError(status.error_message);
  } else {
    // Continue polling
    setTimeout(() => pollStatus(songId), 2000);
  }
};
```

### 3. Download file
```javascript
const downloadSong = (songId) => {
  const link = document.createElement('a');
  link.href = `/api/v3/songs/download/${songId}`;
  link.download = ''; // Browser sẽ dùng filename từ Content-Disposition
  link.click();
};
```

## Database Schema

### Table: songs_v3

```sql
CREATE TABLE songs_v3 (
    id VARCHAR(50) PRIMARY KEY,           -- YouTube video ID
    title VARCHAR(500) NOT NULL,          -- Tiêu đề bài hát
    artist VARCHAR(300),                  -- Nghệ sĩ
    thumbnail_url TEXT NOT NULL,          -- URL thumbnail gốc
    duration INTEGER NOT NULL,            -- Thời lượng (giây)
    duration_formatted VARCHAR(20) NOT NULL, -- Format MM:SS
    keywords TEXT,                        -- Keywords (comma separated)
    original_url TEXT NOT NULL,           -- URL gốc
    status VARCHAR(20) DEFAULT 'pending', -- Processing status
    audio_filename VARCHAR(300),          -- Tên file audio
    thumbnail_filename VARCHAR(300),      -- Tên file thumbnail
    error_message TEXT,                   -- Lỗi (nếu có)
    created_at TIMESTAMP DEFAULT NOW(),   -- Thời gian tạo
    updated_at TIMESTAMP DEFAULT NOW(),   -- Thời gian cập nhật
    completed_at TIMESTAMP                -- Thời gian hoàn thành
);
```

## Advantages V3

### ✅ **Performance**
- Instant response với metadata
- Thumbnail URL gốc = no wait time
- Background processing = non-blocking

### ✅ **Simplicity**  
- 4 endpoints đơn giản
- 1 workflow rõ ràng
- Minimal complexity

### ✅ **User Experience**
- Immediate feedback
- Progress tracking
- Reliable downloads

### ✅ **Developer Experience**
- Easy to implement
- Clear status tracking
- Consistent API responses

### ✅ **Scalability**
- Background task processing
- Efficient file streaming
- Database optimized

## Error Handling

### Common Error Codes:
- `400`: Invalid YouTube URL hoặc yt-dlp error
- `404`: Song not found
- `500`: Server error

### Status Polling Errors:
- Nếu status = `failed`, check `error_message`
- Timeout sau 30 attempts (5 phút)

## Testing

Sử dụng file `test_v3_api.py`:

```bash
python test_v3_api.py
```

Test sẽ kiểm tra:
1. Health check
2. Get song info
3. Status polling  
4. Download streaming
5. Thumbnail access
