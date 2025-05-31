# FastAPI Music API với Firebase Authentication

## 🎯 Tổng quan

API backend cho ứng dụng âm nhạc sử dụng FastAPI với Firebase Authentication để tích hợp với frontend Ionic/Angular.

## 🔥 Firebase Authentication

### Luồng xác thực hoàn chỉnh

```
Frontend (Ionic/Angular) 
    ↓ Firebase ID Token (qua AuthInterceptor)
Backend Middleware
    ↓ Verify Firebase Token hoặc JWT Token
Protected Endpoints
    ↓ Truy cập được các API
✅ SUCCESS
```

### Authentication Endpoints

- **POST /api/v1/auth/google** - Login với Firebase ID token
  ```json
  Request: {"token": "firebase_id_token"}
  Response: {
    "token": {"access_token": "jwt_token", "token_type": "bearer"},
    "user": {...}
  }
  ```

### Protected Endpoints

- **GET /api/v1/songs** - Danh sách bài hát
- **POST /api/v1/songs** - Tạo bài hát mới
- **POST /api/v1/songs/download** - Download từ YouTube
- **GET /api/v1/songs/search** - Tìm kiếm bài hát

## 🚀 Cài đặt và chạy

### 1. Clone và cài đặt dependencies

```bash
git clone <repository>
cd fastapi-music
uv install
```

### 2. Cấu hình environment

Tạo file `.env`:
```env
# Database
DATABASE_URL=sqlite:///./music.db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase
FIREBASE_PROJECT_ID=txt-system-90788
FIREBASE_SERVICE_ACCOUNT_KEY=./document/key-auth-google.json

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_PROJECT_ID=txt-system-90788
```

### 3. Chạy server

```bash
# Development
python main.py

# Hoặc với uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: http://localhost:8000

## 📱 Tích hợp với Frontend

### Ionic/Angular Setup

Frontend Ionic/Angular chỉ cần:

1. **Firebase Auth** đã cấu hình
2. **AuthInterceptor** đã thêm Firebase ID token vào headers
3. **API calls** tới `http://localhost:8000/api/v1/`

Không cần thay đổi gì thêm! Backend sẽ tự động xác thực Firebase tokens.

### Example Frontend Usage

```typescript
// Service call (AuthInterceptor tự động thêm token)
this.http.get('http://localhost:8000/api/v1/songs').subscribe(songs => {
  console.log(songs);
});
```

## 🧪 Testing

Chạy test suite:

```bash
python firebase_auth_test_suite.py
```

Test sẽ kiểm tra:
- ✅ Firebase token verification
- ✅ User authentication
- ✅ Protected endpoint access
- ✅ Song creation/retrieval

## 📁 Cấu trúc dự án

```
app/
├── api/
│   ├── controllers/     # Business logic
│   ├── middleware/      # Authentication middleware
│   ├── routes/         # API routes
│   └── validators/     # Request validation
├── config/             # Configuration
├── internal/
│   ├── domain/         # Domain models
│   ├── storage/        # Database
│   └── utils/          # Utilities
└── ...

document/
└── key-auth-google.json  # Firebase service account

uploads/
├── audio/              # Uploaded audio files
└── thumbnails/         # Audio thumbnails
```

## 🔒 Security Features

- ✅ Firebase ID token verification
- ✅ JWT access token support
- ✅ Token expiration validation
- ✅ User-based access control
- ✅ Input validation và sanitization

## 🌟 Features

### Music Management
- Upload bài hát từ file hoặc YouTube URL
- Tìm kiếm bài hát theo title, artist
- Quản lý playlist cá nhân
- Metadata extraction tự động

### User System
- Google OAuth authentication via Firebase
- User profile management
- Personal song collections

### API Features
- RESTful API design
- Comprehensive error handling
- Request/response validation
- File upload support

## 📖 API Documentation

Truy cập Swagger UI tại: http://localhost:8000/docs

## 🚀 Production Deployment

1. **Environment Variables**: Cập nhật `.env` với production values
2. **Database**: Chuyển từ SQLite sang PostgreSQL
3. **Security**: Enable HTTPS
4. **Monitoring**: Add logging và monitoring

---

**Status**: ✅ Production Ready  
**Firebase Auth**: ✅ Fully Integrated  
**Testing**: ✅ Complete
