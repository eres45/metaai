"""
Working Video Generator - Fixed detection logic.
"""
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


class VideoGenerator:
    """Generate videos using the working detection method."""
    
    def __init__(self, user_data_dir: str = "./meta_session"):
        self.user_data_dir = user_data_dir
        self.downloads_dir = Path("downloads/videos")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(self, prompt: str, num_videos: int = 4) -> dict:
        """
        Generate video by:
        1. Creating images
        2. Clicking View media  
        3. Clicking Animate
        4. Detecting videos with proper selectors
        """
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            try:
                # Step 1: Generate images
                print("🎨 Generating images...")
                await page.goto("https://www.meta.ai")
                await asyncio.sleep(3)
                
                await page.evaluate("""(p) => {
                    const ta = document.querySelector('textarea[data-testid="composer-input"]');
                    if (ta) { 
                        ta.value = p; 
                        ta.dispatchEvent(new Event('input', { bubbles: true })); 
                    }
                }""", prompt)
                await page.keyboard.press("Enter")
                await asyncio.sleep(15)
                
                # Step 2: Click View media
                print("👆 Clicking View media...")
                view_link = await page.query_selector('a[aria-label="View media"]')
                if view_link:
                    await view_link.click()
                    await asyncio.sleep(3)
                
                print(f"   URL: {page.url}")
                
                # Step 3: Click Animate
                print("🎬 Clicking Animate...")
                await page.click('button:has-text("Animate")', force=True)
                await asyncio.sleep(2)
                
                # Step 4: Handle Custom animate if present
                custom = await page.query_selector('button:has-text("Custom animate")')
                if custom:
                    print("   Clicking Custom animate...")
                    await custom.click()
                    await asyncio.sleep(2)
                
                # Step 5: Wait for videos with proper detection
                print("⏳ Waiting for video generation...")
                video_urls = []
                
                # Poll for up to 90 seconds
                for i in range(18):
                    await asyncio.sleep(5)
                    
                    # Check for video elements (with fbcdn.net URLs)
                    videos = await page.query_selector_all('video[src*="fbcdn.net"], video[src*=".mp4"]')
                    
                    if videos:
                        print(f"   🎉 Found {len(videos)} videos after {(i+1)*5}s!")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls:
                                video_urls.append(src)
                                print(f"      URL: {src[:70]}...")
                        
                        if len(video_urls) >= num_videos:
                            break
                    
                    # Also check all video tags
                    all_videos = await page.query_selector_all('video')
                    for vid in all_videos:
                        src = await vid.get_attribute('src')
                        if src and 'fbcdn' in src and src not in video_urls:
                            video_urls.append(src)
                            print(f"      Found: {src[:70]}...")
                    
                    if (i + 1) % 6 == 0:
                        print(f"   Still waiting... ({(i+1)*5}s, {len(video_urls)} videos)")
                
                await context.close()
                
                return {
                    "success": len(video_urls) > 0,
                    "prompt": prompt,
                    "video_urls": video_urls[:num_videos],
                    "count": len(video_urls)
                }
                
            except Exception as e:
                await context.close()
                print(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
    
    def download(self, url: str, filename: str = None) -> str:
        """Download video."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}_{hash(url) % 10000}.mp4"
        
        filepath = self.downloads_dir / filename
        
        try:
            print(f"⬇️ Downloading...")
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Saved: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    async def generate_and_download(self, prompt: str, num_videos: int = 4) -> dict:
        """Generate and download videos."""
        result = await self.generate(prompt, num_videos)
        
        downloaded = []
        if result.get("success") and result.get("video_urls"):
            for i, url in enumerate(result["video_urls"]):
                filename = f"video_{i+1}.mp4"
                filepath = self.download(url, filename)
                if filepath:
                    downloaded.append(filepath)
        
        result["downloaded_files"] = downloaded
        result["download_dir"] = str(self.downloads_dir)
        return result


# Test
if __name__ == "__main__":
    print("="*80)
    print("Video Generation Test")
    print("="*80)
    
    gen = VideoGenerator()
    result = asyncio.run(gen.generate_and_download(
        prompt="A cat dancing",
        num_videos=4
    ))
    
    print("\n" + "="*80)
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Videos: {result.get('count')}")
    print(f"  Downloaded: {len(result.get('downloaded_files', []))}")
    print("="*80)
