"""
Download videos from Meta AI using the returned URLs and cookies.
Run this locally to download videos after generation.
"""
import requests
import json
import sys


def download_video(url, cookies, output_file):
    """Download a single video URL using cookies."""
    session = requests.Session()
    
    # Add all cookies
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain", ""),
            path=cookie.get("path", "/")
        )
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.meta.ai/',
        'Accept': '*/*',
    }
    
    print(f"Downloading to {output_file}...")
    response = session.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f"✅ Downloaded: {output_file} ({len(open(output_file, 'rb').read())} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_videos.py <path_to_storage_state.json>")
        print("\nTo download videos:")
        print("1. Copy the video URLs from the API response")
        print("2. Load your STORAGE_STATE env variable into a file")
        print("3. Run: python download_videos.py storage_state.json")
        sys.exit(1)
    
    storage_file = sys.argv[1]
    
    with open(storage_file) as f:
        storage = json.load(f)
    
    cookies = storage.get("cookies", [])
    print(f"Loaded {len(cookies)} cookies")
    
    # Example - paste your video URLs here
    video_urls = [
        # "https://video-sin... your video url here ..."
    ]
    
    if not video_urls:
        print("\n⚠️  No video URLs set!")
        print("Edit this file and add your video URLs to the video_urls list")
        print("Or paste them when prompted:")
        
        url = input("\nEnter video URL (or press Enter to skip): ").strip()
        while url:
            video_urls.append(url)
            url = input("Enter another URL (or press Enter to finish): ").strip()
    
    for i, url in enumerate(video_urls, 1):
        output_file = f"video_{i}.mp4"
        try:
            download_video(url, cookies, output_file)
        except Exception as e:
            print(f"❌ Failed to download video {i}: {e}")
