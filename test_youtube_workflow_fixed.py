import requests
import json

# Test YouTube download workflow
BASE_URL = "http://localhost:8000"

def test_youtube_download():
    """Test YouTube download workflow mới"""
    
    print("=== Testing YouTube Download Workflow ===")
    
    # Test URL - một video ngắn
    test_url = "https://www.youtube.com/watch?v=SPTUEeGW50E"  # Video ngắn để test
    
    print(f"Testing with URL: {test_url}")
    
    # Test 1: Download video lần đầu (should download to server)
    print("\n1. Testing first download (should download to server)...")
    
    response = requests.post(
        f"{BASE_URL}/api/songs/download",
        json={"url": test_url},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Cached: {data.get('cached')}")
        
        if data.get('data'):
            video_data = data['data']
            print(f"Title: {video_data.get('title')}")
            print(f"Artist: {video_data.get('artist')}")
            print(f"Audio URL: {video_data.get('audio_url')}")
            print(f"Duration: {video_data.get('duration_formatted')}")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "="*50)
    
    # Test 2: Download cùng video lần 2 (should return from cache)
    print("\n2. Testing second download (should return from cache)...")
    
    response2 = requests.post(
        f"{BASE_URL}/api/songs/download",
        json={"url": test_url},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"Success: {data2.get('success')}")
        print(f"Message: {data2.get('message')}")
        print(f"Cached: {data2.get('cached')}")  # Should be True
        
        if data2.get('data'):
            video_data2 = data2['data']
            print(f"Title: {video_data2.get('title')}")
            print(f"Audio URL: {video_data2.get('audio_url')}")
    else:
        print(f"Error: {response2.text}")
    
    print("\n" + "="*50)
    
    # Test 3: Get recent downloads
    print("\n3. Testing recent downloads...")
    
    response3 = requests.get(f"{BASE_URL}/api/songs/recent-downloads?limit=10")
    
    print(f"Status Code: {response3.status_code}")
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"Success: {data3.get('success')}")
        print(f"Number of cached videos: {len(data3.get('data', []))}")
        
        for i, video in enumerate(data3.get('data', [])[:3]):  # Show first 3
            print(f"  {i+1}. {video.get('title')} - {video.get('artist')}")
    else:
        print(f"Error: {response3.text}")

if __name__ == "__main__":
    try:
        test_youtube_download()
    except requests.exceptions.ConnectionError:
        print("Error: Không thể kết nối tới server. Hãy chắc chắn server đang chạy trên http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
