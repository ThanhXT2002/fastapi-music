#!/usr/bin/env python3
"""Test script to verify ffmpeg location detection"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.internal.utils.youtube_downloader import YouTubeDownloader

def test_ffmpeg_location():
    downloader = YouTubeDownloader()
    ffmpeg_location = downloader._get_ffmpeg_location()
    
    print(f"FFmpeg location detected: {ffmpeg_location}")
    
    if ffmpeg_location:
        ffmpeg_exe = os.path.join(ffmpeg_location, "ffmpeg.exe")
        print(f"Full ffmpeg path: {ffmpeg_exe}")
        print(f"File exists: {os.path.exists(ffmpeg_exe)}")
        
        # Check if it's from project
        if "fastapi-music" in ffmpeg_location:
            print("✅ Using project bundled ffmpeg!")
        else:
            print("⚠️  Using system ffmpeg")
    else:
        print("❌ FFmpeg not found!")

if __name__ == "__main__":
    test_ffmpeg_location()
