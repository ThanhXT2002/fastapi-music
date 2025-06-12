import requests
import json

# Test với video mới để xem download workflow
BASE_URL = "http://localhost:8000"

def test_new_video():
    """Test download video mới"""
    
    print("=== Testing New Video Download ===")
    
    # URL video mới (chưa có trong cache)
    new_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - video ngắn
    
    print(f"Testing with new URL: {new_url}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/songs/download",
        json={"url": new_url},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Cached: {data.get('cached')}")  # Should be False (new download)
        
        if data.get('data'):
            video_data = data['data']
            print(f"Title: {video_data.get('title')}")
            print(f"Artist: {video_data.get('artist')}")
            print(f"Audio URL: {video_data.get('audio_url')}")
            print(f"Duration: {video_data.get('duration_formatted')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    try:
        test_new_video()
    except Exception as e:
        print(f"Error: {e}")
