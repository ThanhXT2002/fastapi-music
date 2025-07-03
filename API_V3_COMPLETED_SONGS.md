# 🎵 FastAPI Music Streaming API - V3 Documentation

## ✨ **New Completed Songs Endpoint**### **Direct Streaming URLs**
Các URL này có thể được sử dụng trực tiếp trong:
- HTML5 `<audio>` và `<img>` tags ✅ **STREAMING MODE**
- Video players (VLC, etc.)
- Mobile apps
- Streaming services

**Example:**
```html
<!-- ✅ Audio streaming (mặc định) -->
<audio controls>
  <source src="http://localhost:8000/api/v3/songs/download/dQw4w9WgXcQ" type="audio/mpeg">
</audio>

<!-- ✅ Audio download -->
<a href="http://localhost:8000/api/v3/songs/download/dQw4w9WgXcQ?download=true" download>
  Download MP3
</a>

<!-- ✅ Thumbnail display -->
<img src="http://localhost:8000/api/v3/songs/thumbnail/dQw4w9WgXcQ" alt="Song thumbnail">
```

**URL Parameters:**
- `download=false` (mặc định): Streaming trực tiếp với `Content-Disposition: inline`
- `download=true`: Download file với `Content-Disposition: attachment`# **GET /api/v3/songs/completed**
Lấy tất cả bài hát đã hoàn thành với URL streaming trực tiếp.

**Query Parameters:**
- `limit` (integer, optional): Số lượng bài hát trả về
  - Mặc định: `100`
  - Tối thiểu: `1`
  - Tối đa: `1000`
  - Kiểu dữ liệu: Integer
  - Nếu không hợp lệ: Tự động sử dụng giá trị mặc định

**Examples:**
```bash
# Lấy 100 bài hát mặc định
GET /api/v3/songs/completed

# Lấy 10 bài hát gần nhất
GET /api/v3/songs/completed?limit=10

# Lấy 1 bài hát gần nhất
GET /api/v3/songs/completed?limit=1
```

**Response Format:**
```json
{
  "success": true,
  "message": "Retrieved 2 completed songs (limit: 2)",
  "data": {
    "songs": [
      {
        "id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
        "artist": "Rick Astley",
        "duration": 213,
        "duration_formatted": "03:33",
        "thumbnail_url": "http://localhost:8000/api/v3/songs/thumbnail/dQw4w9WgXcQ",
        "audio_url": "http://localhost:8000/api/v3/songs/download/dQw4w9WgXcQ",
        "keywords": ["Music", "rick astley", "Never Gonna Give You Up", "nggyu", "never gonna give you up lyrics", "rick rolled"]
      }
    ],
    "total": 2
  }
}
```

**Response Fields:**
- `id`: YouTube video ID
- `title`: Tên bài hát
- `artist`: Tên ca sĩ/kênh
- `duration`: Thời lượng (giây)
- `duration_formatted`: Thời lượng định dạng MM:SS
- `thumbnail_url`: URL streaming thumbnail từ server (luôn khả dụng)
- `audio_url`: URL streaming audio từ server (luôn khả dụng)
- `keywords`: Danh sách từ khóa

## 🎯 **Use Cases**

### 1. **Music Player Frontend**
```javascript
// Lấy danh sách bài hát
const response = await fetch('/api/v3/songs/completed');
const data = await response.json();

// Tạo playlist
data.data.songs.forEach(song => {
  const audioElement = document.createElement('audio');
  audioElement.src = song.audio_url;
  audioElement.controls = true;
  
  const thumbnail = document.createElement('img');
  thumbnail.src = song.thumbnail_url;
  thumbnail.alt = song.title;
  
  // Add to playlist...
});
```

### 2. **Mobile App Integration**
```javascript
// React Native example
const playlistData = await fetch('http://your-server.com/api/v3/songs/completed')
  .then(res => res.json());

// ✅ Use audio_url for streaming (auto inline mode)
<Audio source={{ uri: song.audio_url }} />

// ✅ Download functionality
const downloadUrl = `${song.audio_url}?download=true`;
```

### 3. **Direct Streaming URLs**
Các URL này có thể được sử dụng trực tiếp trong:
- HTML5 `<audio>` tags
- Video players (VLC, etc.)
- Mobile apps
- Streaming services

## 🎵 **Angular/Frontend Integration Examples**

### **Angular Component Example:**
```typescript
// music-player.component.ts
import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-music-player',
  template: `
    <div *ngFor="let song of songs" class="song-item">
      <img [src]="song.thumbnail_url" [alt]="song.title" class="thumbnail">
      <div class="song-info">
        <h3>{{ song.title }}</h3>
        <p>{{ song.artist }} - {{ song.duration_formatted }}</p>
        
        <!-- ✅ Streaming Audio Player -->
        <audio controls [src]="song.audio_url">
          Your browser does not support the audio element.
        </audio>
        
        <!-- ✅ Download Button -->
        <a [href]="getDownloadUrl(song.audio_url)" download class="download-btn">
          Download
        </a>
      </div>
    </div>
  `
})
export class MusicPlayerComponent implements OnInit {
  songs: any[] = [];

  async ngOnInit() {
    const response = await fetch('/api/v3/songs/completed?limit=20');
    const data = await response.json();
    this.songs = data.data.songs;
  }

  getDownloadUrl(audioUrl: string): string {
    return `${audioUrl}?download=true`;
  }
}
```

### **Vue.js Example:**
```vue
<template>
  <div v-for="song in songs" :key="song.id" class="song-card">
    <img :src="song.thumbnail_url" :alt="song.title" class="thumbnail">
    <h3>{{ song.title }}</h3>
    <p>{{ song.artist }}</p>
    
    <!-- ✅ Streaming -->
    <audio controls :src="song.audio_url"></audio>
    
    <!-- ✅ Download -->
    <a :href="`${song.audio_url}?download=true`" download>Download</a>
  </div>
</template>

<script>
export default {
  data() {
    return {
      songs: []
    };
  },
  async mounted() {
    const response = await fetch('/api/v3/songs/completed');
    const data = await response.json();
    this.songs = data.data.songs;
  }
};
</script>
```

### **React Example:**
```jsx
import React, { useState, useEffect } from 'react';

function MusicPlayer() {
  const [songs, setSongs] = useState([]);

  useEffect(() => {
    async function loadSongs() {
      const response = await fetch('/api/v3/songs/completed');
      const data = await response.json();
      setSongs(data.data.songs);
    }
    loadSongs();
  }, []);

  return (
    <div>
      {songs.map(song => (
        <div key={song.id} className="song-card">
          <img src={song.thumbnail_url} alt={song.title} className="thumbnail" />
          <h3>{song.title}</h3>
          <p>{song.artist} - {song.duration_formatted}</p>
          
          {/* ✅ Streaming */}
          <audio controls src={song.audio_url}>
            Your browser does not support the audio element.
          </audio>
          
          {/* ✅ Download */}
          <a href={`${song.audio_url}?download=true`} download>
            Download
          </a>
        </div>
      ))}
    </div>
  );
}
```

## 🔧 **Technical Features**

### **Optimized Performance**
- ✅ **Quick Database Check**: Kiểm tra database trước khi gọi YouTube API
- ✅ **Reduced Latency**: Bài hát đã tải từ 30s xuống 1-2s
- ✅ **Database Indexes**: Indexes cho `status`, `created_at`
- ✅ **File Pattern Matching**: Tự động tìm file audio với nhiều pattern

### **Streaming Capabilities**
- ✅ **Chunked Streaming**: Stream file theo chunks 8KB
- ✅ **Resume Support**: Hỗ trợ `Accept-Ranges: bytes`
- ✅ **Proper Headers**: Content-Type, Content-Length, Content-Disposition
- ✅ **Error Handling**: Xử lý lỗi file không tồn tại
- ✅ **Unified URLs**: Chỉ cần 2 URL cho audio và thumbnail

### **Cross-Platform Support**
- ✅ **CORS Enabled**: Hỗ trợ cross-origin requests
- ✅ **Multiple Formats**: M4A, MP3, WebM
- ✅ **Thumbnail Formats**: JPG, PNG, WebP

## 🔧 **Limit Parameter Features**

### **Smart Validation**
- ✅ **Type Safety**: Chỉ chấp nhận integer
- ✅ **Range Validation**: 1-1000 bài hát
- ✅ **Default Value**: 100 bài hát nếu không chỉ định
- ✅ **Error Messages**: Thông báo lỗi rõ ràng cho giá trị không hợp lệ

### **Use Cases**
```javascript
// Lấy 10 bài hát mới nhất cho homepage
const latest = await fetch('/api/v3/songs/completed?limit=10');

// Lấy 1 bài hát ngẫu nhiên
const random = await fetch('/api/v3/songs/completed?limit=1');

// Lấy tất cả bài hát cho admin panel
const all = await fetch('/api/v3/songs/completed?limit=1000');

// Pagination example
const page1 = await fetch('/api/v3/songs/completed?limit=20'); // Page 1
// Note: Để pagination hoàn chỉnh, cần thêm offset parameter
```

## 🧪 **Testing**

### **Web Test Page**
Truy cập: `http://localhost:8000/test`

### **API Test**
```bash
# PowerShell - Lấy 100 bài hát mặc định
Invoke-WebRequest -Uri "http://localhost:8000/api/v3/songs/completed" -Method GET

# PowerShell - Lấy 5 bài hát gần nhất
Invoke-WebRequest -Uri "http://localhost:8000/api/v3/songs/completed?limit=5" -Method GET

# curl (if available)
curl -X GET "http://localhost:8000/api/v3/songs/completed?limit=10"
```

### **Validation Examples**
```bash
# ✅ Valid requests
GET /api/v3/songs/completed?limit=1       # Returns 1 song
GET /api/v3/songs/completed?limit=50      # Returns 50 songs
GET /api/v3/songs/completed?limit=1000    # Returns 1000 songs (max)

# ❌ Invalid requests (auto-corrected by FastAPI)
GET /api/v3/songs/completed?limit=0       # Error: Input should be >= 1
GET /api/v3/songs/completed?limit=1001    # Error: Input should be <= 1000
GET /api/v3/songs/completed?limit=abc     # Error: Invalid integer
GET /api/v3/songs/completed?limit=-5      # Error: Input should be >= 1
```

### **Direct Streaming Test**
```bash
# Test audio streaming
curl -I "http://localhost:8000/api/v3/songs/download/dQw4w9WgXcQ"

# Test thumbnail streaming
curl -I "http://localhost:8000/api/v3/songs/thumbnail/dQw4w9WgXcQ"
```

## 📊 **Performance Improvements**

| Scenario | Before | After | Improvement |
|----------|--------|--------|-------------|
| **Existing Song** | 30s | 1-2s | **93% faster** |
| **New Song** | 10s | 10s | Same |
| **Database Query** | No indexes | 3 indexes | **Faster lookups** |
| **File Finding** | Single pattern | Multiple patterns | **More reliable** |

## 🚀 **Next Steps**

1. **Pagination**: Thêm `offset` parameter để pagination hoàn chỉnh
2. **Search**: Tìm kiếm theo title, artist, keywords
3. **Sorting**: Sắp xếp theo ngày, tên, thời lượng, views
4. **Filtering**: Lọc theo artist, duration, keywords
5. **Caching**: Cache kết quả API với Redis
6. **CDN**: Tích hợp CDN cho streaming tốt hơn

### **Pagination Example (Future)**
```bash
# Page 1: 20 bài hát đầu tiên
GET /api/v3/songs/completed?limit=20&offset=0

# Page 2: 20 bài hát tiếp theo
GET /api/v3/songs/completed?limit=20&offset=20

# Page 3: 20 bài hát tiếp theo
GET /api/v3/songs/completed?limit=20&offset=40
```
