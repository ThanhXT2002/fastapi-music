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
from pathlib import Path
from sqlalchemy.orm import Session


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
    
    def __init__(self):
        super().__init__()
        print("🚀 YouTubeCacheAdmin initialized!")
    
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
    
    def _delete_associated_files(self, cache_record: YouTubeCache):
        """Delete thumbnail and audio files associated with YouTube cache record"""
        files_deleted = []
        
        try:
            print(f"🔍 Starting file deletion for video ID: {cache_record.video_id}")
            print(f"📄 Thumbnail URL: {cache_record.thumbnail_url}")
            print(f"🎵 Audio URL: {cache_record.audio_url}")
            
            # Lấy đường dẫn gốc của project - sửa lại để đúng với cấu trúc
            current_file = Path(__file__)  # app/config/admin.py
            project_root = current_file.parent.parent.parent  # Đi lên 3 cấp
            uploads_dir = project_root / "uploads"
            
            print(f"📁 Current file: {current_file}")
            print(f"📁 Project root: {project_root}")
            print(f"📁 Uploads directory: {uploads_dir}")
            print(f"📁 Uploads exists: {uploads_dir.exists()}")
            
            # Xóa thumbnail file nếu có
            thumbnail_dir = uploads_dir / "thumbnails"
            print(f"🖼️ Thumbnail directory: {thumbnail_dir}")
            print(f"🖼️ Thumbnail dir exists: {thumbnail_dir.exists()}")
            
            if thumbnail_dir.exists():
                # Liệt kê tất cả file trong thư mục thumbnail
                all_thumbnails = list(thumbnail_dir.glob("*"))
                print(f"🖼️ All thumbnail files: {[f.name for f in all_thumbnails]}")
                
                # Tìm file thumbnail theo video_id
                matching_thumbnails = list(thumbnail_dir.glob(f"{cache_record.video_id}_*"))
                print(f"🎯 Matching thumbnails for '{cache_record.video_id}': {[f.name for f in matching_thumbnails]}")
                
                for thumbnail_file in matching_thumbnails:
                    if thumbnail_file.is_file():
                        try:
                            print(f"🗑️ Attempting to delete thumbnail: {thumbnail_file}")
                            thumbnail_file.unlink()
                            files_deleted.append(str(thumbnail_file))
                            print(f"✅ Successfully deleted thumbnail: {thumbnail_file.name}")
                        except PermissionError as e:
                            print(f"🔒 Permission denied deleting {thumbnail_file}: {str(e)}")
                        except Exception as e:
                            print(f"❌ Failed to delete thumbnail {thumbnail_file}: {str(e)}")
            else:
                print(f"⚠️ Thumbnail directory does not exist: {thumbnail_dir}")
            
            # Xóa audio file nếu có
            audio_dir = uploads_dir / "audio"
            print(f"🎵 Audio directory: {audio_dir}")
            print(f"🎵 Audio dir exists: {audio_dir.exists()}")
            
            if audio_dir.exists():
                # Liệt kê tất cả file trong thư mục audio
                all_audio = list(audio_dir.glob("*"))
                print(f"🎵 All audio files: {[f.name for f in all_audio]}")
                
                # Tìm file audio theo video_id
                matching_audio = list(audio_dir.glob(f"{cache_record.video_id}_*"))
                print(f"🎯 Matching audio for '{cache_record.video_id}': {[f.name for f in matching_audio]}")
                
                for audio_file in matching_audio:
                    if audio_file.is_file():
                        try:
                            print(f"🗑️ Attempting to delete audio: {audio_file}")
                            audio_file.unlink()
                            files_deleted.append(str(audio_file))
                            print(f"✅ Successfully deleted audio: {audio_file.name}")
                        except PermissionError as e:
                            print(f"🔒 Permission denied deleting {audio_file}: {str(e)}")
                        except Exception as e:
                            print(f"❌ Failed to delete audio {audio_file}: {str(e)}")
            else:
                print(f"⚠️ Audio directory does not exist: {audio_dir}")
                            
        except Exception as e:
            print(f"❌ Error deleting files for video {cache_record.video_id}: {str(e)}")
            import traceback
            print(f"🔧 Full traceback: {traceback.format_exc()}")
            
        print(f"📊 Total files deleted: {len(files_deleted)}")
        return files_deleted
          
    async def on_model_delete(self, data: dict, request: Request) -> None:
        """Hook gọi trước khi xóa model - cleanup files"""
        try:
            print(f"\n🗑️ ===== ON_MODEL_DELETE HOOK TRIGGERED =====")
            print(f"📊 Data received: {data}")
            
            # Lấy thông tin record từ database
            session = Session(engine)
            try:
                cache_record = session.get(YouTubeCache, data.get('id'))
                if cache_record:
                    print(f"📝 Found record: {cache_record.title}")
                    print(f"🎬 Video ID: {cache_record.video_id}")
                    
                    # Xóa các file liên quan
                    deleted_files = self._delete_associated_files(cache_record)
                    
                    print(f"📋 Summary: Deleted {len(deleted_files)} files")
                else:
                    print(f"⚠️ No cache record found with ID: {data.get('id')}")
                    
            finally:
                session.close()
                
            print(f"🗑️ ===== ON_MODEL_DELETE COMPLETE =====\n")
            
        except Exception as e:
            print(f"❌ Error in on_model_delete: {str(e)}")
            import traceback
            print(f"🔧 Full error traceback: {traceback.format_exc()}")
    
    async def delete_model(self, request: Request, pk: str):
        """Override delete_model method"""
        print(f"\n🔥 DELETE_MODEL CALLED - PK: {pk}")
        await self._cleanup_files_by_pk(pk)
        return await super().delete_model(request, pk)
    
    async def delete(self, request: Request, pk: str):
        """Override delete method"""
        print(f"\n🗑️ DELETE METHOD CALLED - PK: {pk}")
        await self._cleanup_files_by_pk(pk)
        return await super().delete(request, pk)
    
    async def _cleanup_files_by_pk(self, pk: str):
        """Cleanup files by primary key"""
        session = Session(engine)
        try:
            cache_record = session.get(YouTubeCache, pk)
            if cache_record:
                print(f"📝 Found record by PK: {cache_record.title} (Video: {cache_record.video_id})")
                self._delete_associated_files(cache_record)
            else:
                print(f"⚠️ No record found with PK: {pk}")
        finally:
            session.close()
    
    async def _cleanup_files_by_data(self, data: dict):
        """Cleanup files by data dict"""
        session = Session(engine)
        try:
            record_id = data.get('id')
            if record_id:
                cache_record = session.get(YouTubeCache, record_id)
                if cache_record:
                    print(f"📝 Found record by data: {cache_record.title} (Video: {cache_record.video_id})")
                    self._delete_associated_files(cache_record)
                else:
                    print(f"⚠️ No record found with ID from data: {record_id}")
        finally:
            session.close()


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
