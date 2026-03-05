"""
Meta AI Video Generator using main chat interface.
"""
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


class MetaVideoGenerator:
    """Generate videos using Meta AI chat interface."""
    
    def __init__(self, user_data_dir: str = "./meta_session"):
        self.user_data_dir = user_data_dir
        self.downloads_dir = Path("downloads/videos")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_video(self, prompt: str, num_videos: int = 1) -> dict:
        """
        Generate video using Meta AI main chat.
        Uses prompt like "Generate a video of..." to trigger video generation.
        """
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            try:
                # Navigate to main Meta AI page
                print("Opening Meta AI...")
                await page.goto("https://www.meta.ai")
                await asyncio.sleep(3)
                
                # Format prompt for video generation
                video_prompt = f"Generate a video: {prompt}"
                print(f"Sending prompt: {video_prompt}")
                
                # Fill the chat input
                await page.evaluate("""(prompt) => {
                    const textarea = document.querySelector('textarea[data-testid="composer-input"]');
                    if (textarea) {
                        textarea.value = prompt;
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", video_prompt)
                
                await page.keyboard.press("Enter")
                print("Prompt submitted, waiting for generation...")
                
                # Wait longer for video generation (can take 60-120 seconds)
                video_urls = []
                
                for attempt in range(30):  # 2.5 minutes total
                    await asyncio.sleep(5)
                    
                    # Check for video elements
                    videos = await page.query_selector_all('video')
                    if videos:
                        print(f"Found {len(videos)} video elements after {(attempt+1)*5}s")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls:
                                video_urls.append(src)
                                print(f"  Video URL: {src[:60]}...")
                        
                        if len(video_urls) >= num_videos:
                            break
                    
                    # Also check for video links
                    links = await page.query_selector_all('a[href*=".mp4"], a[href*="video"]')
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and href not in video_urls:
                            video_urls.append(href)
                    
                    if (attempt + 1) % 6 == 0:  # Every 30 seconds
                        print(f"  Still waiting... ({(attempt+1)*5}s elapsed)")
                
                await page.screenshot(path="debug_video_result.png")
                
                await context.close()
                
                return {
                    "success": len(video_urls) > 0,
                    "prompt": prompt,
                    "video_urls": video_urls[:num_videos],
                    "count": len(video_urls)
                }
                
            except Exception as e:
                await context.close()
                print(f"Error: {e}")
                return {"success": False, "error": str(e)}
    
    def download_video(self, url: str, filename: str = None) -> str:
        """Download video from URL."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}_{hash(url) % 10000}.mp4"
        
        filepath = self.downloads_dir / filename
        
        try:
            print(f"Downloading video from {url[:60]}...")
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded: {filepath}")
            return str(filepath)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    async def generate_and_download(self, prompt: str, num_videos: int = 1) -> dict:
        """Generate video and download it."""
        result = await self.generate_video(prompt, num_videos)
        
        downloaded = []
        if result.get("success") and result.get("video_urls"):
            for i, url in enumerate(result["video_urls"]):
                filename = f"video_{i+1}.mp4"
                filepath = self.download_video(url, filename)
                if filepath:
                    downloaded.append(filepath)
        
        result["downloaded_files"] = downloaded
        result["download_dir"] = str(self.downloads_dir)
        return result


# Test
if __name__ == "__main__":
    print("="*80)
    print("Meta AI Video Generation")
    print("="*80)
    
    generator = MetaVideoGenerator()
    
    result = asyncio.run(generator.generate_and_download(
        prompt="A cat playing piano in a cozy jazz club with soft lighting",
        num_videos=1
    ))
    
    print("\n" + "="*80)
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Videos found: {result.get('count')}")
    print(f"  Downloaded: {len(result.get('downloaded_files', []))}")
    for url in result.get('video_urls', []):
        print(f"  URL: {url[:70]}...")
    print("="*80)
