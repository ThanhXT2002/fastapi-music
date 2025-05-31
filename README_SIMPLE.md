# FastAPI Music API với Firebase Authentication

API backend cho ứng dụng âm nhạc sử dụng FastAPI với Firebase Authentication, tích hợp hoàn hảo với frontend Ionic/Angular.

## 🚀 Quick Start

```bash
# Cài đặt dependencies
uv install

# Chạy server
python main.py
```

Server chạy tại: http://localhost:8000

## 🔥 Firebase Authentication

- ✅ **Tích hợp Firebase**: Xác thực trực tiếp với Firebase ID tokens từ frontend
- ✅ **Dual Token Support**: Hỗ trợ cả Firebase ID tokens và JWT access tokens  
- ✅ **Auto Integration**: Frontend Ionic/Angular hoạt động ngay lập tức
- ✅ **Production Ready**: Đầy đủ security và error handling

## 🎵 Features

### Music Management
- **YouTube Download**: Tải nhạc từ YouTube với metadata
- **Search**: Tìm kiếm bài hát theo title, artist
- **Library**: Quản lý thư viện nhạc cá nhân
- **Favorites**: Đánh dấu yêu thích và lịch sử phát

### Authentication  
- **Firebase Auth**: Google OAuth thông qua Firebase
- **User Management**: Tự động tạo/quản lý user accounts
- **Protected APIs**: Bảo vệ endpoints với authentication middleware

## 📱 API Endpoints

### Authentication
- `POST /api/v1/auth/google` - Login with Firebase token

### Songs
- `GET /api/v1/songs` - Get user's songs
- `POST /api/v1/songs` - Create new song
- `POST /api/v1/songs/download` - Download from YouTube
- `GET /api/v1/songs/search` - Search songs

## 🧪 Testing

```bash
# Run Firebase auth test suite
python firebase_auth_test_suite.py
```

## 📖 Documentation

- **API Docs**: http://localhost:8000/docs
- **Detailed Setup**: Xem `README_MAIN.md` để biết chi tiết đầy đủ

---

**Status**: ✅ Production Ready với Firebase Authentication
