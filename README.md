# FastAPI Music Download API

Một API đơn giản cho việc tải nhạc từ YouTube với Firebase Authentication.

## 🚀 Khởi động nhanh

```bash
# Cài đặt dependencies
uv install

# Chạy server
python main.py
```

# vào môi trường venv:
.venv\Scripts\activate


Server chạy tại: http://localhost:8000

## 🔥 Tính năng

- **Xác thực Firebase**: Đăng nhập bằng Google OAuth thông qua Firebase
- **Tải nhạc YouTube**: Tải và lưu trữ nhạc từ URL YouTube
- **Metadata**: Tự động trích xuất thông tin bài hát (title, artist, duration, thumbnail)

## 📱 API Endpoints

### Authentication
- `POST /api/v1/auth/google` - Đăng nhập với Firebase token

### Songs
- `POST /api/v1/songs/download` - Tải nhạc từ YouTube

## 🛠️ Cấu trúc dự án

```
app/
├── api/                    # API layer
│   ├── controllers/        # Business logic
│   ├── routes/            # Endpoint definitions  
│   ├── validators/        # Request/Response models
│   └── middleware/        # Auth middleware
├── config/                # Database & app config
└── internal/              # Core business logic
    ├── domain/            # Data models
    ├── storage/           # Database repositories
    └── utils/             # Helper utilities
```

## 🔧 Cấu hình

Tạo file `.env`:
```env
FIREBASE_PROJECT_ID=your-project-id
DATABASE_URL=sqlite:///music.db
UPLOAD_DIRECTORY=./uploads
```

## 📝 Sử dụng API

### 1. Xác thực
```bash
POST /api/v1/auth/google
{
  "token": "firebase_id_token"
}
```

### 2. Tải nhạc
```bash
POST /api/v1/songs/download
Authorization: Bearer jwt_token
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "quality": "best"
}
```

## 🧪 Test

```bash
# Chạy test Firebase authentication
python firebase_auth_test_suite.py
```
