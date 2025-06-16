from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from app.config.database import engine
from app.config.config import settings
from app.internal.model.user import User
from app.internal.model.song import Song
from app.internal.model.youtube_cache import YouTubeCache
import bcrypt
import os


class AdminAuth(AuthenticationBackend):
    """
    Secure authentication backend for admin panel using environment variables
    """
    
    def __init__(self, secret_key: str):
        super().__init__(secret_key)
        # Create default admin password hash if not set
        if not settings.ADMIN_PASSWORD_HASH:
            # Default password: "secure123!" - CHANGE THIS!
            default_password = "secure123!"
            self.default_password_hash = bcrypt.hashpw(
                default_password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            print(f"⚠️  WARNING: Using default admin password. Please set ADMIN_PASSWORD_HASH environment variable!")
            print(f"Default credentials - Username: {settings.ADMIN_USERNAME}, Password: {default_password}")
        else:
            self.default_password_hash = None
    
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        # Check username
        if username != settings.ADMIN_USERNAME:
            return False
            
        # Check password
        password_hash = settings.ADMIN_PASSWORD_HASH or self.default_password_hash
        
        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            request.session.update({"authenticated": True, "username": username})
            return True
            
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("authenticated", False)


class UserAdmin(ModelView, model=User):
    """Admin view for User model"""
    column_list = [
        User.id, 
        User.email, 
        User.name, 
        User.is_active, 
        User.is_verified,
        User.created_at
    ]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.id, User.email, User.name, User.created_at]
    column_default_sort = [(User.created_at, True)]  # Sort by created_at descending
    
    # Form configurations
    form_columns = [
        User.email, 
        User.name, 
        User.profile_picture,
        User.is_active, 
        User.is_verified,
        User.google_id
    ]
    
    # Display configurations
    column_labels = {
        User.id: "ID",
        User.email: "Email",
        User.name: "Tên",
        User.profile_picture: "Ảnh đại diện",
        User.is_active: "Hoạt động",
        User.is_verified: "Đã xác minh",
        User.created_at: "Ngày tạo",
        User.google_id: "Google ID"
    }
    
    # Pagination
    page_size = 20
    page_size_options = [10, 20, 50, 100]


class SongAdmin(ModelView, model=Song):
    """Admin view for Song model"""
    column_list = [
        Song.id,
        Song.title,
        Song.artist,
        Song.album,
        Song.duration,
        Song.is_favorite,
        Song.created_at
    ]
    column_searchable_list = [Song.title, Song.artist, Song.album]
    column_sortable_list = [Song.title, Song.artist, Song.duration, Song.created_at]
    column_default_sort = [(Song.created_at, True)]
    
    # Form configurations
    form_columns = [
        Song.id,
        Song.title,
        Song.artist,
        Song.album,
        Song.duration,
        Song.thumbnail_url_cloudinary,
        Song.audio_url_cloudinary,
        Song.thumbnail_local_path,
        Song.audio_local_path,
        Song.is_favorite,
        Song.keywords,
        Song.source_url
    ]
    
    # Display configurations
    column_labels = {
        Song.id: "ID",
        Song.title: "Tiêu đề",
        Song.artist: "Nghệ sĩ",
        Song.album: "Album",
        Song.duration: "Thời lượng (giây)",
        Song.thumbnail_url_cloudinary: "Thumbnail Cloudinary",
        Song.audio_url_cloudinary: "Audio Cloudinary",
        Song.thumbnail_local_path: "Thumbnail Local",
        Song.audio_local_path: "Audio Local",
        Song.is_favorite: "Yêu thích",
        Song.keywords: "Từ khóa",
        Song.source_url: "URL nguồn",
        Song.created_at: "Ngày tạo"
    }
    
    # Pagination
    page_size = 20
    page_size_options = [10, 20, 50, 100]


class YouTubeCacheAdmin(ModelView, model=YouTubeCache):
    """Admin view for YouTube Cache model"""
    column_list = [
        YouTubeCache.id,
        YouTubeCache.video_id,
        YouTubeCache.title,
        YouTubeCache.artist,
        YouTubeCache.duration_formatted,
        YouTubeCache.created_at
    ]
    column_searchable_list = [
        YouTubeCache.video_id, 
        YouTubeCache.title, 
        YouTubeCache.artist
    ]
    column_sortable_list = [
        YouTubeCache.title, 
        YouTubeCache.artist, 
        YouTubeCache.duration, 
        YouTubeCache.created_at
    ]
    column_default_sort = [(YouTubeCache.created_at, True)]
    
    # Form configurations
    form_columns = [
        YouTubeCache.video_id,
        YouTubeCache.title,
        YouTubeCache.artist,
        YouTubeCache.thumbnail_url,
        YouTubeCache.duration,
        YouTubeCache.duration_formatted,
        YouTubeCache.keywords,
        YouTubeCache.original_url,
        YouTubeCache.audio_url,
        YouTubeCache.user_id
    ]
    
    # Display configurations
    column_labels = {
        YouTubeCache.id: "ID",
        YouTubeCache.video_id: "Video ID",
        YouTubeCache.title: "Tiêu đề",
        YouTubeCache.artist: "Nghệ sĩ",
        YouTubeCache.thumbnail_url: "Thumbnail URL",
        YouTubeCache.duration: "Thời lượng (giây)",
        YouTubeCache.duration_formatted: "Thời lượng",
        YouTubeCache.keywords: "Từ khóa",
        YouTubeCache.original_url: "URL gốc",
        YouTubeCache.audio_url: "Audio URL",
        YouTubeCache.user_id: "User ID",
        YouTubeCache.created_at: "Ngày tạo"
    }
    
    # Pagination
    page_size = 20
    page_size_options = [10, 20, 50, 100]


def setup_admin(app):
    """Setup admin panel for the FastAPI app"""
    
    # Create admin instance with secure configuration
    admin = Admin(
        app, 
        engine,
        title="🎵 Music Admin Panel",
        logo_url="https://fastapi.tiangolo.com/img/icon-white.svg",
        authentication_backend=AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
    )
    
    # Add model views
    admin.add_view(UserAdmin)
    admin.add_view(SongAdmin)
    admin.add_view(YouTubeCacheAdmin)
    
    return admin
