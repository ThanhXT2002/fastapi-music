# 🎵 FastAPI Music Download API

Một API mạnh mẽ và hiện đại để tải nhạc từ YouTube với Firebase Authentication, được xây dựng bằng FastAPI và SQLAlchemy.

## ✨ Tính năng chính

- 🔐 **Firebase Authentication**: Xác thực an toàn với Google OAuth
- 🎬 **YouTube Download**: Tải audio chất lượng cao từ YouTube
- 📊 **Smart Cache**: Hệ thống cache thông minh tránh tải trùng lặp
- 🗄️ **Database**: SQLAlchemy ORM với hỗ trợ PostgreSQL/SQLite
- ☁️ **Cloud Storage**: Tích hợp Cloudinary cho CDN (sẵn sàng)
- 📱 **RESTful API**: API chuẩn REST với documentation tự động
- 🚀 **Performance**: Async/await và background tasks
- 📈 **Scalable**: Kiến trúc Clean Architecture

## 🚀 Khởi động nhanh

### 1. Clone và cài đặt
```bash
git clone <repository-url>
cd fastapi-music

# Tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Cài đặt dependencies
pip install -r requirements.txt
# hoặc sử dụng uv (khuyến nghị)
uv install
```

### 2. Cấu hình môi trường
Tạo file `.env` trong thư mục gốc:
```env
# Database
DATABASE_URL=sqlite:///./fastapi_music.db
# DATABASE_URL=postgresql://user:password@localhost/dbname

# JWT Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase Authentication
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_KEY=./document/key-auth-google.json

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_PROJECT_ID=your-google-project-id

# File Storage
BASE_URL=http://localhost:8000
UPLOAD_DIRECTORY=./uploads
AUDIO_DIRECTORY=./uploads/audio
THUMBNAIL_DIRECTORY=./uploads/thumbnails

# Cloudinary (optional)
CLOUDINARY_CLOUD_NAME=your-cloudinary-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret
```

### 3. Chạy ứng dụng
```bash
python main.py
```

Server sẽ chạy tại: **http://localhost:8000**

- 📚 **API Docs**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- ❤️ **Health Check**: http://localhost:8000/api/v1/health

## 📱 API Endpoints

### 🔐 Authentication (`/api/v1/auth`)
```http
POST /api/v1/auth/google
Content-Type: application/json

{
  "token": "firebase_id_token_here"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "User Name",
    "profile_picture": "https://...",
    "firebase_uid": "firebase_user_id"
  }
}
```

### 🎵 Songs (`/api/v1/songs`)

#### Tải nhạc từ YouTube
```http
POST /api/v1/songs/download
Authorization: Bearer jwt_token
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Downloaded successfully",
  "data": {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "artist": "Rick Astley",
    "duration": 213,
    "thumbnail_url": "http://localhost:8000/thumbnails/dQw4w9WgXcQ.jpg",
    "audio_url": "http://localhost:8000/audio/dQw4w9WgXcQ_1234567890.m4a",
    "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "created_at": "2025-06-12T10:30:00Z"
  }
}
```

#### Lấy danh sách tải gần đây
```http
GET /api/v1/songs/recent-downloads?limit=20
Authorization: Bearer jwt_token
```

### 🏥 Health Check
```http
GET /api/v1/health

Response:
{
  "status": "ok",
  "message": "FastAPI Music API is running",
  "database": {
    "type": "SQLite",
    "status": "connected"
  }
}
```

## 🏗️ Kiến trúc dự án

```
fastapi-music/
├── 📄 main.py                    # Entry point
├── 📄 requirements.txt           # Dependencies
├── 📄 .env                      # Environment config
├── 📂 app/
│   ├── 📂 api/                  # API Layer
│   │   ├── 📂 controllers/      # Business Logic Controllers
│   │   │   ├── auth.py          # Authentication controller
│   │   │   └── song.py          # Song download controller
│   │   ├── 📂 routes/           # API Routes
│   │   │   ├── router.py        # Main router
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   └── song.py          # Song endpoints
│   │   ├── 📂 validators/       # Pydantic Models
│   │   │   ├── auth.py          # Auth request/response models
│   │   │   └── youtube.py       # YouTube models
│   │   └── 📂 middleware/       # Custom Middleware
│   │       └── auth.py          # JWT Authentication
│   ├── 📂 config/               # Configuration
│   │   ├── config.py            # App settings
│   │   └── database.py          # Database setup
│   └── 📂 internal/             # Core Business Logic
│       ├── 📂 model/            # Database Models
│       │   ├── user.py          # User model
│       │   ├── song.py          # Song model
│       │   ├── youtube_cache.py # Cache model
│       │   ├── user_songs.py    # Many-to-many relationship
│       │   └── errors.py        # Custom exceptions
│       ├── 📂 storage/          # Data Access Layer
│       │   └── 📂 repositories/ # Repository pattern
│       │       ├── repository.py     # Base repository
│       │       ├── user.py           # User repository
│       │       └── youtube_cache.py  # Cache repository
│       ├── 📂 rfc/              # Standards & Protocols
│       │   └── 📂 jwt/          # JWT implementation
│       │       └── jwt.py       # JWT utilities
│       └── 📂 utils/            # Utilities
│           ├── youtube_service.py    # Main YouTube service
│           ├── youtube_downloader.py # Download logic
│           ├── cloudinary_service.py # Cloud storage
│           └── helpers.py            # Firebase helpers
├── 📂 document/                 # Documentation
│   └── key-auth-google.json     # Firebase service account
└── 📂 uploads/                  # Local file storage
    ├── 📂 audio/                # Audio files
    └── 📂 thumbnails/           # Thumbnail images
```

## 🛠️ Công nghệ sử dụng

### Backend Framework
- **FastAPI** - Modern, fast web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM

### Authentication & Security
- **Firebase Admin SDK** - User authentication
- **PyJWT** - JWT token handling
- **python-jose** - JWT utilities

### Media Processing
- **yt-dlp** - YouTube downloader
- **Cloudinary** - Cloud media management

### Database
- **SQLite** (development)
- **PostgreSQL** (production ready)
- **psycopg2** - PostgreSQL adapter

## 🔧 Cấu hình nâng cao

### Database Migration
```bash
# Khởi tạo database
python -c "from app.config.database import create_tables; create_tables()"

# Hoặc sử dụng endpoint
curl -X GET http://localhost:8000/api/v1/init-db
```

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./fastapi_music.db` |
| `SECRET_KEY` | JWT secret key | Required |
| `FIREBASE_PROJECT_ID` | Firebase project ID | Required |
| `BASE_URL` | API base URL | `http://localhost:8000` |
| `UPLOAD_DIRECTORY` | Upload directory | `./uploads` |

### Production Deployment
```bash
# Using Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker (create Dockerfile)
docker build -t fastapi-music .
docker run -p 8000:8000 fastapi-music
```

## 🧪 Testing

### Chạy test Firebase Authentication
```bash
python firebase_auth_test_suite.py
```

### Test API với cURL
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Download YouTube video (need valid JWT token)
curl -X POST http://localhost:8000/api/v1/songs/download \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
```

## 📊 Features Deep Dive

### 🎯 Smart Caching System
- Kiểm tra cache trước khi download
- Tránh tải trùng lặp cùng một video
- Metadata được lưu trong database
- File được serve trực tiếp từ local storage

### 🔄 Background Processing
- Download files không block API response
- Upload lên Cloudinary chạy background
- Graceful error handling

### 🌐 CDN Integration
- Cloudinary integration sẵn sàng
- Automatic image optimization
- Global CDN delivery
- Fallback to local storage

### 🔐 Security Features
- Firebase Authentication
- JWT token validation
- CORS configuration
- Input validation với Pydantic

## 🚨 Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check database URL
echo $DATABASE_URL

# Reset database
rm fastapi_music.db
python -c "from app.config.database import create_tables; create_tables()"
```

**2. Firebase Authentication Error**
```bash
# Check Firebase config
ls -la document/key-auth-google.json

# Verify project ID
echo $FIREBASE_PROJECT_ID
```

**3. YouTube Download Error**
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Check video availability
yt-dlp --list-formats "https://youtube.com/watch?v=VIDEO_ID"
```

## 📈 Performance & Scaling

### Current Capabilities
- ⚡ Async FastAPI framework
- 🗄️ SQLAlchemy connection pooling  
- 📱 RESTful API design
- 🔄 Background task processing

### Scaling Recommendations
- Use PostgreSQL for production
- Implement Redis for caching
- Add rate limiting
- Use Celery for heavy background tasks
- Deploy with Docker + Kubernetes

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

- 📧 Email: [your-email@example.com]
- 🐛 Issues: [GitHub Issues](link-to-issues)
- 📖 Documentation: [API Docs](http://localhost:8000/docs)

---

**⭐ Nếu project này hữu ích, hãy cho một star nhé! ⭐**
