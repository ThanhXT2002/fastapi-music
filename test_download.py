"""
Test script để kiểm tra tính năng download thumbnail mới

Chạy script này để test:
python test_download.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.internal.utils.youtube_downloader import YouTubeDownloader

def test_download_with_thumbnail():
    """Test download audio và thumbnail"""
    downloader = YouTubeDownloader()
    
    # Test với một video YouTube
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll cho test
    
    print("=== Testing Download Audio + Thumbnail ===")
    print(f"URL: {test_url}")
    print()
    
    result = downloader.download_audio_to_server(test_url)
    
    if result["success"]:
        print("✅ Download thành công!")
        print(f"📁 Audio path: {result['video_data']['audio_url']}")
        print(f"🖼️ Thumbnail path: {result['video_data'].get('local_thumbnail_url', 'Không có')}")
        print(f"📝 Title: {result['video_data']['title']}")
        print(f"👤 Artist: {result['video_data']['artist']}")
        print(f"⏱️ Duration: {result['video_data']['duration_formatted']}")
        print(f"📦 File size: {result['video_data']['file_size'] / (1024*1024):.2f} MB")
    else:
        print("❌ Download thất bại!")
        print(f"Lỗi: {result['message']}")

if __name__ == "__main__":
    test_download_with_thumbnail()
