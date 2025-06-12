import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from typing import Dict, Optional, Tuple
from pathlib import Path
from app.config.config import settings

class CloudinaryService:
    def __init__(self):
        """Initialize Cloudinary configuration"""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
    
    def upload_audio(self, file_path: str, filename: str) -> Dict:
        """
        Upload audio file to Cloudinary
        
        Args:
            file_path: Local path to audio file
            filename: Unique filename for the upload
            
        Returns:
            Dict with upload result containing URL, public_id, etc.
        """
        try:
            # Audio upload options
            upload_options = {
                'public_id': f"music_app/audio/{filename}",
                'resource_type': 'video',  # Audio files use 'video' resource type
                'folder': 'music_app/audio',
                'use_filename': False,
                'unique_filename': True,
                'overwrite': False,
                'format': 'm4a',
                'quality': 'auto',
                'tags': ['music', 'audio', 'youtube_download']
            }
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file_path, **upload_options)
            
            return {
                'success': True,
                'url': result.get('secure_url'),
                'public_id': result.get('public_id'),
                'format': result.get('format'),
                'duration': result.get('duration'),
                'bytes': result.get('bytes'),
                'created_at': result.get('created_at'),
                'resource_type': result.get('resource_type')
            }
            
        except Exception as e:
            print(f"Error uploading audio to Cloudinary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_thumbnail(self, file_path: str, filename: str) -> Dict:
        """
        Upload thumbnail image to Cloudinary
        
        Args:
            file_path: Local path to thumbnail file
            filename: Unique filename for the upload
            
        Returns:
            Dict with upload result containing URL, public_id, etc.
        """
        try:
            # Image upload options
            upload_options = {
                'public_id': f"music_app/thumbnails/{filename}",
                'resource_type': 'image',
                'folder': 'music_app/thumbnails',
                'use_filename': False,
                'unique_filename': True,
                'overwrite': False,
                'quality': 'auto:good',
                'format': 'webp',  # Convert to WebP for better compression
                'transformation': [
                    {'width': 800, 'height': 600, 'crop': 'limit'},  # Max size
                    {'quality': 'auto:good'}
                ],
                'tags': ['music', 'thumbnail', 'youtube_download']
            }
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file_path, **upload_options)
            
            return {
                'success': True,
                'url': result.get('secure_url'),
                'public_id': result.get('public_id'),
                'format': result.get('format'),
                'width': result.get('width'),
                'height': result.get('height'),
                'bytes': result.get('bytes'),
                'created_at': result.get('created_at'),
                'resource_type': result.get('resource_type')
            }
            
        except Exception as e:
            print(f"Error uploading thumbnail to Cloudinary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_media_files(self, audio_path: str, thumbnail_path: Optional[str], base_filename: str) -> Dict:
        """
        Upload both audio and thumbnail files to Cloudinary
        
        Args:
            audio_path: Local path to audio file
            thumbnail_path: Local path to thumbnail file (optional)
            base_filename: Base filename for both files
            
        Returns:
            Dict with both upload results
        """
        result = {
            'audio': None,
            'thumbnail': None,
            'success': False,
            'errors': []
        }
        
        try:            # Upload audio file
            if audio_path and os.path.exists(audio_path):
                audio_result = self.upload_audio(audio_path, base_filename)
                result['audio'] = audio_result
                
                if not audio_result.get('success'):
                    result['errors'].append(f"Audio upload failed: {audio_result.get('error')}")
            else:
                result['errors'].append("Audio file not found")
                
            # Upload thumbnail file if exists
            if thumbnail_path and os.path.exists(thumbnail_path):
                thumbnail_result = self.upload_thumbnail(thumbnail_path, base_filename)
                result['thumbnail'] = thumbnail_result
                
                if not thumbnail_result.get('success'):
                    result['errors'].append(f"Thumbnail upload failed: {thumbnail_result.get('error')}")
            
            # Check overall success - prioritize audio success
            audio_success = result['audio'] and result['audio'].get('success')
            thumbnail_success = not thumbnail_path or (result['thumbnail'] and result['thumbnail'].get('success'))
            
            # Mark as success if audio uploads successfully (thumbnail is optional)
            result['success'] = audio_success
            
            if audio_success and not thumbnail_success:
                result['message'] = 'Audio uploaded successfully, but thumbnail upload failed'
            elif audio_success and thumbnail_success:
                result['message'] = 'Both audio and thumbnail uploaded successfully'
            else:
                result['message'] = 'Audio upload failed'
            
            return result
            
        except Exception as e:
            result['errors'].append(f"Upload process failed: {str(e)}")
            return result
    
    def delete_file(self, public_id: str, resource_type: str = 'image') -> Dict:
        """
        Delete file from Cloudinary
        
        Args:
            public_id: Cloudinary public ID of the file
            resource_type: Type of resource ('image', 'video', 'raw')
            
        Returns:
            Dict with deletion result
        """
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            
            return {
                'success': result.get('result') == 'ok',
                'result': result.get('result'),
                'public_id': public_id
            }
            
        except Exception as e:
            print(f"Error deleting file from Cloudinary: {e}")
            return {
                'success': False,
                'error': str(e),
                'public_id': public_id
            }
    def cleanup_local_files(self, file_paths_or_audio_path, thumbnail_path: Optional[str] = None) -> Dict:
        """
        Clean up local files after successful upload
        
        Args:
            file_paths_or_audio_path: Can be a single audio path or a list of file paths to delete
            thumbnail_path: Local thumbnail file path (only used if file_paths_or_audio_path is a single path)
            
        Returns:
            Dict with cleanup results
        """
        result = {
            'files_deleted': [],
            'errors': []
        }
        
        try:
            # Handle list of file paths (new preferred way)
            if isinstance(file_paths_or_audio_path, list):
                for file_path in file_paths_or_audio_path:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            result['files_deleted'].append(file_path)
                            print(f"Deleted local file: {file_path}")
                        except Exception as e:
                            error_msg = f"Error deleting file {file_path}: {str(e)}"
                            result['errors'].append(error_msg)
                            print(error_msg)
            
            # Handle individual audio/thumbnail paths (legacy way)
            else:
                audio_path = file_paths_or_audio_path
                
                # Delete audio file
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    result['files_deleted'].append(audio_path)
                    print(f"Deleted local audio file: {audio_path}")
                
                # Delete thumbnail file
                if thumbnail_path and os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
                    result['files_deleted'].append(thumbnail_path)
                    print(f"Deleted local thumbnail file: {thumbnail_path}")
                
        except Exception as e:
            error_msg = f"Error cleaning up local files: {str(e)}"
            result['errors'].append(error_msg)
            print(error_msg)
        
        return result
