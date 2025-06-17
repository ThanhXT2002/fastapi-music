import requests
import time
import json

# Base URL
BASE_URL = "http://localhost:8000"
V3_BASE = f"{BASE_URL}/api/v3"

def test_v3_with_new_song():
    """Test V3 with a new song"""
    
    # Test data - different video
    youtube_url = "https://youtu.be/tB4zbIUFIkI"  # A different video
    
    print("=== Testing FastAPI Music V3 - New Song ===\n")
    
    # Step 1: Get song info
    print("1. Getting song info...")
    response = requests.post(f"{V3_BASE}/songs/info", json={
        "youtube_url": youtube_url
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['message']}")
        song_info = data['data']
        song_id = song_info['id']
        print(f"   Song ID: {song_id}")
        print(f"   Title: {song_info['title']}")
        print(f"   Artist: {song_info['artist']}")
        print(f"   Duration: {song_info['duration_formatted']}")
        print()
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return
    
    # Step 2: Poll status
    print("2. Polling status...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"   Attempt {attempt}/{max_attempts}")
        
        response = requests.get(f"{V3_BASE}/songs/status/{song_id}")
        
        if response.status_code == 200:
            status_data = response.json()['data']
            status = status_data['status']
            progress = status_data.get('progress', 0)
            
            print(f"   Status: {status} ({progress*100:.0f}%)")
            
            if status == "completed":
                print("✅ Download completed!")
                print(f"   Audio filename: {status_data.get('audio_filename')}")
                break
            elif status == "failed":
                error = status_data.get('error_message', 'Unknown error')
                print(f"❌ Download failed: {error}")
                return
            else:
                print("   Still processing... waiting 5 seconds")
                time.sleep(5)
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return
    
    if attempt >= max_attempts:
        print("❌ Timeout waiting for download to complete")
        return
    
    print()
    
    # Step 3: Test download
    print("3. Testing download...")
    response = requests.get(f"{V3_BASE}/songs/download/{song_id}", stream=True)
    
    if response.status_code == 200:
        content_length = response.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            print(f"✅ Download ready! File size: {size_mb:.2f} MB")
        else:
            print("✅ Download ready! (Size unknown)")
        
        # Test streaming (download first 1MB)
        downloaded = 0
        chunk_count = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                downloaded += len(chunk)
                chunk_count += 1
                if downloaded >= 1024 * 1024:  # Stop after 1MB
                    break
        
        print(f"   Downloaded {downloaded} bytes in {chunk_count} chunks")
        print("✅ Streaming download works!")
    else:
        print(f"❌ Download failed: {response.status_code} - {response.text}")
        return
    
    print()
    print("=== V3 Test Complete ===")

if __name__ == "__main__":
    test_v3_with_new_song()
