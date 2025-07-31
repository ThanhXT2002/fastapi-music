
# 🎵 FastAPI Music Download API

API hiện đại tải nhạc từ YouTube, xác thực Firebase, xây dựng với FastAPI & SQLAlchemy. Hỗ trợ cache thông minh, lưu trữ local/CDN, bảo mật JWT, tích hợp Cloudinary, kiến trúc sạch, dễ mở rộng.

---

## ✨ Tính năng chính

- 🔐 Xác thực Google OAuth qua Firebase
- 🎬 Tải audio chất lượng cao từ YouTube (yt-dlp)
- 📊 Cache thông minh, tránh tải trùng
- 🗄️ ORM SQLAlchemy, hỗ trợ SQLite & PostgreSQL
- ☁️ Tích hợp Cloudinary (CDN, tối ưu ảnh)
- 📱 RESTful API, docs tự động
- 🚀 Async/await, background tasks
- 📈 Clean Architecture, dễ mở rộng

---

## 🚀 Khởi động nhanh

### 1. Clone & cài đặt

```bash
git clone <repository-url>
cd fastapi-music

python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
# hoặc dùng uv (nếu có)
uv install
```

### 2. Cấu hình môi trường

Tạo file `.env` ở thư mục gốc, ví dụ:

```env
DATABASE_URL=sqlite:///./fastapi_music.db
# Hoặc PostgreSQL: postgresql://user:password@localhost/dbname
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_KEY=./document/key-auth-google.json
BASE_URL=http://localhost:8000
UPLOAD_DIRECTORY=./uploads
AUDIO_DIRECTORY=./uploads/audio
THUMBNAIL_DIRECTORY=./uploads/thumbnails
CLOUDINARY_CLOUD_NAME=your-cloudinary-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret
```

### 3. Khởi tạo database

```bash
python -c "from app.config.database import create_tables; create_tables()"
```
Hoặc dùng endpoint:
```bash
curl -X GET http://localhost:8000/api/v1/init-db
```

### 4. Chạy ứng dụng

```bash
python main.py
```
Hoặc production:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
# hoặc Docker
docker build -t fastapi-music .
docker run -p 8000:8000 fastapi-music
```

---

## 📱 API Endpoints

### 🔐 Auth (`/api/v1/auth`)

```http
POST /api/v1/auth/google
{
  "token": "firebase_id_token_here"
}
```
Trả về: access_token, user info.

### 🎵 Songs (`/api/v1/songs`)

- **POST /download**: Tải nhạc từ YouTube (yêu cầu JWT)
- **POST /info**: Lấy info bài hát từ YouTube
- **GET /status/{song_id}**: Trạng thái tải bài hát
- **GET /recent-downloads**: Danh sách tải gần đây

### 🎶 YTMusic (`/api/v1/ytmusic`)

- **GET /stream/{song_id}**: Stream audio trực tiếp từ YouTube Music
- **GET /search**: Tìm kiếm bài hát, album, nghệ sĩ, playlist
- **GET /song/{song_id}**: Lấy metadata bài hát
- **GET /playlist-with-song/{song_id}**: Lấy playlist liên quan

### 🏥 Health Check

```http
GET /api/v1/health
```
Trả về trạng thái server, database.

---

## 🏗️ Cấu trúc dự án

```
fastapi-music/
├── main.py
├── requirements.txt
├── .env
├── app/
│   ├── config/         # config.py, database.py
│   ├── controllers/    # auth, song, ytmusic
│   ├── routes/         # router, auth, song, ytmusic
│   ├── schemas/        # Pydantic models
│   ├── models/         # SQLAlchemy models
│   ├── services/       # youtube_service, ytmusic_service
│   ├── internal/       # rfc, storage, utils
├── document/           # Tài liệu, key-auth-google.json
├── uploads/            # audio/, thumbnails/
```

---

## � Biến môi trường

| Variable                | Description                | Default                        |
|-------------------------|----------------------------|-------------------------------|
| `DATABASE_URL`          | Database connection string | `sqlite:///./fastapi_music.db` |
| `SECRET_KEY`            | JWT secret key             | Required                       |
| `ALGORITHM`             | JWT algorithm              | HS256                          |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry (minutes)  | 30                             |
| `FIREBASE_PROJECT_ID`   | Firebase project ID        | Required                       |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | Firebase key file   | ./document/key-auth-google.json|
| `BASE_URL`              | API base URL               | http://localhost:8000          |
| `UPLOAD_DIRECTORY`      | Upload directory           | ./uploads                      |
| `AUDIO_DIRECTORY`       | Audio files directory      | ./uploads/audio                |
| `THUMBNAIL_DIRECTORY`   | Thumbnails directory       | ./uploads/thumbnails           |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name      | (optional)                     |
| `CLOUDINARY_API_KEY`    | Cloudinary API key         | (optional)                     |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret      | (optional)                     |

---

## 🛠️ Công nghệ sử dụng

- **FastAPI** (backend)
- **Uvicorn** (ASGI server)
- **Pydantic** (data validation)
- **SQLAlchemy** (ORM)
- **Firebase Admin SDK** (auth)
- **PyJWT**, **python-jose** (JWT)
- **yt-dlp** (YouTube download)
- **Cloudinary** (CDN)
- **SQLite** (dev), **PostgreSQL** (prod)

---

## � Tính năng nâng cao

- 🎯 **Smart Caching**: Kiểm tra cache, tránh tải trùng, metadata lưu DB, serve file local.
- 🔄 **Background Processing**: Download/Upload chạy nền, không block API.
- 🌐 **CDN Integration**: Cloudinary sẵn sàng, tối ưu ảnh, fallback local.
- 🔐 **Security**: Xác thực Firebase, JWT, CORS, input validation.
- ⚡ **Async**: Xử lý bất đồng bộ, background tasks.

---

## 🧪 Testing

- Test Firebase Auth:  
  ```bash
  python firebase_auth_test_suite.py
  ```
- Test API với cURL:
  ```bash
  curl http://localhost:8000/api/v1/health
  curl -X POST http://localhost:8000/api/v1/songs/download \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
  ```

---

##  Troubleshooting

**Database Error**  
- Kiểm tra biến DATABASE_URL  
- Reset DB:  
  ```bash
  rm fastapi_music.db
  python -c "from app.config.database import create_tables; create_tables()"
  ```

**Firebase Auth Error**  
- Kiểm tra file `document/key-auth-google.json`  
- Kiểm tra `FIREBASE_PROJECT_ID`

**YouTube Download Error**  
- Cập nhật yt-dlp: `pip install --upgrade yt-dlp`
- Kiểm tra video: `yt-dlp --list-formats "https://youtube.com/watch?v=VIDEO_ID"`

---

## 📈 Performance & Scaling

- ⚡ Async FastAPI
- 🗄️ SQLAlchemy connection pooling
-  Background task processing
- RESTful API design

**Khuyến nghị mở rộng:**
- Dùng PostgreSQL cho production
- Redis cache
- Rate limiting
- Celery cho background tasks nặng
- Docker + Kubernetes

---

## 🤝 Đóng góp

1. Fork repo
2. Tạo branch mới
3. Commit & push
4. Mở Pull Request

---

## 📄 License

MIT License

---

## 📞 Hỗ trợ

- Email: tranxuanthanhtxt2002@gmail.com
