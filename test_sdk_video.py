"""
Try using metaai-api SDK for video generation.
"""
import sys
import json
sys.path.insert(0, 'metaai-api/src')

from metaai_api import MetaAI

# Load cookies
cookies = json.load(open('meta_cookies.json'))
print(f"Loaded cookies: {list(cookies.keys())}")

# Initialize MetaAI
try:
    ai = MetaAI(cookies=cookies)
    print("✅ MetaAI initialized")
    
    # Try to generate a video
    print("\nGenerating video...")
    result = ai.generate_video_new("A cat dancing")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # If successful, download videos
    if result.get('success') and result.get('video_urls'):
        import requests
        from pathlib import Path
        from datetime import datetime
        
        Path("downloads/videos").mkdir(parents=True, exist_ok=True)
        
        for i, url in enumerate(result['video_urls']):
            print(f"\nDownloading video {i+1}...")
            try:
                response = requests.get(url, stream=True, timeout=120)
                if response.status_code == 200:
                    filepath = f"downloads/videos/sdk_video_{i+1}_{datetime.now().strftime('%H%M%S')}.mp4"
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Saved: {filepath}")
                else:
                    print(f"❌ HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
