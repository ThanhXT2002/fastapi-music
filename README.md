# FastAPI Music API

Một hệ thống API Music hoàn chỉnh được xây dựng bằng FastAPI, cung cấp các tính năng quản lý nhạc và tải nhạc từ YouTube.

## 🚀 Tính năng chính

### 🎵 Quản lý nhạc
- **Tải nhạc từ YouTube**: Chỉ cần một click với link YouTube
- **Đồng bộ nhạc**: Backup dữ liệu nhạc từ SQLite của frontend
- **Quản lý thư viện**: Tạo, sửa, xóa bài hát
- **Tìm kiếm**: Tìm kiếm theo tên bài hát, nghệ sĩ, album
- **Yêu thích**: Đánh dấu bài hát yêu thích
- **Lịch sử phát**: Theo dõi số lần phát và thời gian phát gần nhất

### 🔐 Xác thực
- **Google OAuth**: Đăng nhập bằng Google
- **JWT Token**: Quản lý session an toàn
- **Optional Auth**: API hoạt động cả với và không có đăng nhập

### 📁 Quản lý file
- **Audio Storage**: Lưu trữ file nhạc đã tải
- **Thumbnail**: Lưu trữ ảnh thumbnail
- **Static Serving**: Phục vụ file tĩnh qua HTTP

## 🏗️ Kiến trúc

Dự án tuân theo **Clean Architecture** với cấu trúc như sau:

```
fastapi-music/
├── app/
│   ├── api/                    # API Layer
│   │   ├── controllers/        # Business logic
│   │   │   ├── auth.py
│   │   │   └── song.py
│   │   ├── middleware/         # Middleware (Auth, CORS, etc.)
│   │   │   └── auth.py
│   │   ├── routes/            # API Routes
│   │   │   ├── auth.py
│   │   │   ├── song.py
│   │   │   └── router.py
│   │   └── validators/        # Request/Response models
│   │       ├── auth.py
│   │       └── song.py
│   ├── config/                # Configuration
│   │   ├── config.py
│   │   └── database.py
│   └── internal/              # Internal logic
│       ├── domain/            # Domain models
│       │   ├── user.py
│       │   ├── song.py
│       │   └── errors.py
│       ├── rfc/              # RFC implementations
│       │   └── jwt/
│       ├── storage/          # Data access
│       │   └── repositories/
│       └── utils/            # Utilities
│           ├── helpers.py
│           └── youtube_downloader.py
├── uploads/                   # File storage
│   ├── audio/
│   └── thumbnails/
├── main.py                   # Entry point
└── requirements.txt          # Dependencies
```

## 📊 Database Schema

### User Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    profile_picture VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    google_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Song Table
```sql
CREATE TABLE songs (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    artists TEXT,              -- JSON array
    album VARCHAR(255),
    duration INTEGER NOT NULL, -- seconds
    genre TEXT,               -- JSON array
    release_date VARCHAR(50),
    
    -- Media files
    thumbnail_url VARCHAR(500),
    audio_url VARCHAR(500),
    local_path VARCHAR(500),
    
    -- Lyrics
    lyrics TEXT,
    has_lyrics BOOLEAN DEFAULT FALSE,
    
    -- Download info
    is_downloaded BOOLEAN DEFAULT FALSE,
    downloaded_at TIMESTAMP,
    
    -- User interaction
    is_favorite BOOLEAN DEFAULT FALSE,
    play_count INTEGER DEFAULT 0,
    last_played_at TIMESTAMP,
    
    -- Metadata
    keywords TEXT,            -- JSON array
    source VARCHAR(50) DEFAULT 'youtube',
    bitrate INTEGER,
    language VARCHAR(10),
    
    -- Relations
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠️ Cài đặt

### Yêu cầu hệ thống
- Python 3.9+
- uv (Python package manager)
- FFmpeg (cho yt-dlp)

### Bước 1: Clone repository
```bash
git clone <repository-url>
cd fastapi-music
```

### Bước 2: Cài đặt dependencies
```bash
uv sync
```

### Bước 3: Cấu hình environment
```bash
# Copy file cấu hình mẫu
cp .env.example .env

# Chỉnh sửa .env với thông tin của bạn
# Đặc biệt là Google OAuth credentials
```

### Bước 4: Chạy server
```bash
uv run python main.py
```

Server sẽ chạy tại: `http://localhost:8000`

## 📖 API Documentation

### Authentication Endpoints

#### POST `/api/v1/auth/google`
Đăng nhập bằng Google OAuth

**Request:**
```json
{
  "token": "google_id_token"
}
```

**Response:**
```json
{
  "token": {
    "access_token": "jwt_token",
    "token_type": "bearer"
  },
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "name": "User Name",
    "profile_picture": "https://...",
    "is_verified": true
  }
}
```

### Song Endpoints

#### GET `/api/v1/songs/`
Lấy danh sách bài hát
- **Authenticated**: Trả về bài hát của user
- **Anonymous**: Trả về bài hát public

**Query Parameters:**
- `skip`: int = 0 (pagination)
- `limit`: int = 100 (pagination)

#### POST `/api/v1/songs/download`
Tải nhạc từ YouTube

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "download_audio": true,
  "quality": "best"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Song downloaded successfully",
  "song": { /* Song object */ },
  "download_path": "/uploads/audio/..."
}
```

#### POST `/api/v1/songs/sync`
Đồng bộ nhạc từ frontend (yêu cầu đăng nhập)

**Request:**
```json
{
  "songs": [
    {
      "title": "Song Title",
      "artist": "Artist Name",
      "duration": 240,
      /* ... other song fields */
    }
  ]
}
```

#### GET `/api/v1/songs/search`
Tìm kiếm bài hát

**Query Parameters:**
- `q`: string (từ khóa tìm kiếm)
- `skip`: int = 0
- `limit`: int = 50

#### POST `/api/v1/songs/{song_id}/favorite`
Đánh dấu/bỏ đánh dấu yêu thích (yêu cầu đăng nhập)

#### POST `/api/v1/songs/{song_id}/play`
Phát nhạc (tăng play count)

## 🔧 Cấu hình

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite:///./music.db

# JWT
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_PROJECT_ID=your-project-id

# File Storage
UPLOAD_DIRECTORY=./uploads
AUDIO_DIRECTORY=./uploads/audio
THUMBNAIL_DIRECTORY=./uploads/thumbnails

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### Google OAuth Setup

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Kích hoạt Google+ API
4. Tạo OAuth 2.0 credentials
5. Thêm redirect URIs:
   - `http://localhost:8000/api/auth/google/callback`
   - `http://127.0.0.1:8000/api/auth/google/callback`

## 🎯 Use Cases

### 1. User không đăng nhập
- Tải nhạc từ YouTube về server
- Tìm kiếm và phát nhạc public
- Xem thông tin bài hát

### 2. User đã đăng nhập
- Tất cả tính năng của user không đăng nhập
- Đồng bộ thư viện nhạc từ frontend
- Quản lý bài hát yêu thích
- Theo dõi lịch sử phát nhạc
- Backup dữ liệu cá nhân

## 🔄 Workflow

### Tải nhạc từ YouTube
1. User gửi link YouTube
2. System extract thông tin video
3. Download audio bằng yt-dlp
4. Lưu file và metadata vào database
5. Trả về thông tin bài hát

### Đồng bộ nhạc
1. User đăng nhập
2. Gửi danh sách bài hát từ SQLite local
3. System bulk insert vào database
4. Trả về kết quả sync

## 🚨 Lưu ý

- **FFmpeg**: Cần cài đặt FFmpeg để yt-dlp hoạt động
- **Storage**: File nhạc sẽ được lưu trong thư mục `uploads/`
- **Performance**: Tải nhạc có thể mất thời gian tùy vào chất lượng internet
- **Legal**: Chỉ tải nhạc có bản quyền hoặc được phép

## 📈 Tương lai

- [ ] Playlist management
- [ ] Music streaming
- [ ] Lyrics integration
- [ ] Social features (share, comment)
- [ ] Music recommendation
- [ ] Mobile app support
- [ ] Advanced search filters
- [ ] Audio effects and equalizer

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

---

**Developed with ❤️ by Your Team**
│   │   │   ├── auth.py
│   │   │   └── user.py
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── cors.py
│   │   │   └── logging.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── post.py
│   │   │   ├── auth.py
│   │   │   ├── router.py
│   │   │   └── user.py
│   │   │
│   │   └── validators/
│   │       ├── __init__.py
│   │       ├── post.py
│   │       ├── auth.py
│   │       ├── base.py
│   │       └── user.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── server.py
│   │
│   └── internal/
│       ├── __init__.py
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── post.py
│       │   ├── errors.py
│       │   └── user.py
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── crypto.py
│       │   ├── helpers.py
│       │   └── validator.py
│       │
│       ├── rfc/
│       │   ├── __init__.py
│       │   └── jwt/
│       │       ├── __init__.py
│       │       └── jwt.py
│       │
│       └── storage/
│           ├── __init__.py
│           │
│           ├── cache/
│           │   ├── __init__.py
│           │   └── redis.py
│           │
│           ├── database/
│           │   ├── __init__.py
│           │   └── database.py
│           │
│           └── repositories/
│               ├── __init__.py
│               ├── post.py
│               ├── repository.py
│               └── user.py
│
├── tests/
│   ├── __init__.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api.py
│   │
│   └── unit/
│       ├── __init__.py
│       │
│       ├── controllers/
│       │   ├── __init__.py
│       │   └── test_user.py
│       │
│       └── repositories/
│           ├── __init__.py
│           └── test_user.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── main.py   


Giải thích cấu trúc
app/ - Thư mục chính của ứng dụng

api/ - Chứa tất cả logic API

controllers/ - Xử lý business logic
middleware/ - Các middleware cho authentication, CORS, logging
routes/ - Định nghĩa các route endpoints
validators/ - Validation cho input data


config/ - Cấu hình ứng dụng

config.py - Cấu hình chung
database.py - Cấu hình database
server.py - Cấu hình server


internal/ - Logic nội bộ ứng dụng

domain/ - Domain models và business logic
utils/ - Các utility functions
rfc/ - Implementations theo RFC standards (JWT, etc.)
storage/ - Data access layer

cache/ - Redis caching
database/ - Database connections
repositories/ - Data repository pattern





tests/ - Thư mục test

integration/ - Integration tests
unit/ - Unit tests cho từng component

Root files

main.py - Entry point của ứng dụng
.env.example - Template cho environment variables
requirements.txt - Dependencies production
requirements-dev.txt - Dependencies development
README.md - Tài liệu dự án
.gitignore - Git ignore rules

Lợi ích của cấu trúc này

Separation of Concerns - Mỗi thành phần có trách nhiệm riêng biệt
Scalability - Dễ dàng mở rộng khi dự án lớn lên
Testability - Cấu trúc rõ ràng cho việc viết test
Maintainability - Dễ bảo trì và debug
Clean Architecture - Tuân thủ nguyên tắc clean code

Ví dụ sử dụng
python# main.py
from fastapi import FastAPI
from app.api.routes.router import api_router
from app.config.config import settings

app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)


Các điểm mạnh của cấu trúc này:

  -Phân tách rõ ràng - API layer, business logic, và data access được tách biệt hoàn toàn
  -Middleware layer - Có sẵn authentication, CORS, logging middleware
  -Validation layer - Validators riêng biệt cho từng entity
  -Repository pattern - Abstraction layer cho data access
  -Testing structure - Cả unit tests và integration tests
  -Caching support - Redis integration sẵn sàng
  -JWT implementation - Tuân thủ RFC standards