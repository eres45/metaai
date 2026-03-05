"""
Test direct video generation with "Generate a video of..." prompt.
"""
import asyncio
import requests
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime


async def test_direct_video():
    """Test generating video directly with video-specific prompt."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        print("Testing direct video generation...")
        
        # Go to main page
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        print(f"URL: {page.url}")
        
        # Submit video prompt with specific format
        video_prompt = "Generate a video of a cat playing piano in a jazz club"
        print(f"\nSending: {video_prompt}")
        
        await page.evaluate("""(prompt) => {
            const ta = document.querySelector('textarea[data-testid="composer-input"]');
            if (ta) { 
                ta.value = prompt; 
                ta.dispatchEvent(new Event('input', { bubbles: true })); 
            }
        }""", video_prompt)
        
        await page.keyboard.press("Enter")
        print("Prompt submitted")
        
        # Wait and poll for videos
        video_urls = []
        for i in range(30):  # 150 seconds total
            await asyncio.sleep(5)
            
            # Check for video elements with fbcdn URLs
            videos = await page.query_selector_all('video')
            print(f"  [{i+1}] Video elements: {len(videos)}")
            
            for vid in videos:
                src = await vid.get_attribute('src')
                if src:
                    print(f"      Video src: {src[:70]}...")
                    if 'fbcdn' in src or 'video-sin' in src:
                        if src not in video_urls:
                            video_urls.append(src)
                            print(f"      🎉 NEW VIDEO URL!")
            
            # Check for download links
            links = await page.query_selector_all('a[href*=".mp4"], a[href*="video"]')
            if links:
                print(f"      Video links found: {len(links)}")
            
            if len(video_urls) > 0 and (i + 1) % 6 == 0:
                print(f"  Progress: {len(video_urls)} videos after {(i+1)*5}s")
                await page.screenshot(path=f"debug_video_direct_{(i+1)*5}s.png")
        
        await page.screenshot(path="debug_video_direct_final.png")
        
        # Download videos if found
        if video_urls:
            print(f"\n✅ SUCCESS! Found {len(video_urls)} videos")
            
            Path("downloads/videos").mkdir(parents=True, exist_ok=True)
            
            for i, url in enumerate(video_urls[:4]):
                print(f"\nDownloading video {i+1}...")
                try:
                    response = requests.get(url, stream=True, timeout=120)
                    if response.status_code == 200:
                        filepath = f"downloads/videos/direct_video_{i+1}_{datetime.now().strftime('%H%M%S')}.mp4"
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"✅ Saved: {filepath}")
                    else:
                        print(f"❌ HTTP {response.status_code}")
                except Exception as e:
                    print(f"❌ Error: {e}")
        else:
            print("\n❌ No videos found after 150 seconds")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Direct Video Generation Test")
    print("="*80)
    asyncio.run(test_direct_video())
