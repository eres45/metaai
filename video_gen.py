"""
Meta AI Video Generator - Using "Create video" button workflow.
"""
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


class VideoGenerator:
    """Generate videos using Meta AI 'Create video' workflow."""
    
    def __init__(self, user_data_dir: str = "./meta_session"):
        self.user_data_dir = user_data_dir
        self.downloads_dir = Path("downloads/videos")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(self, prompt: str, num_videos: int = 1) -> dict:
        """
        Generate video using Meta AI Create video workflow.
        
        Steps:
        1. Go to https://www.meta.ai
        2. Click "Create video" button
        3. Enter prompt in the prompt box
        4. Submit and wait for generation
        """
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            try:
                # Step 1: Go to main Meta AI page
                print("Opening Meta AI...")
                await page.goto("https://www.meta.ai")
                await asyncio.sleep(3)
                
                # Step 2: Click "Create video" button
                print("Looking for 'Create video' button...")
                
                # Try to find and click the Create video button
                clicked = False
                for selector in [
                    'button:has-text("Create video")',
                    'a:has-text("Create video")',
                    '[data-testid] button:has-text("Create video")',
                ]:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=5000)
                        if btn:
                            await btn.click()
                            print(f"✅ Clicked 'Create video' with selector: {selector}")
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    # Try JavaScript
                    result = await page.evaluate("""() => {
                        const elements = Array.from(document.querySelectorAll('button, a'));
                        const btn = elements.find(e => e.textContent && e.textContent.includes('Create video'));
                        if (btn) {
                            btn.click();
                            return 'clicked';
                        }
                        return 'not-found';
                    }""")
                    print(f"JS click result: {result}")
                    clicked = (result == 'clicked')
                
                if not clicked:
                    return {"success": False, "error": "Could not find 'Create video' button"}
                
                # Wait for UI to update after clicking
                print("Waiting for UI to update...")
                await asyncio.sleep(5)
                print(f"Current URL after click: {page.url}")
                
                # Take screenshot to see current state
                await page.screenshot(path="debug_after_create_video.png")
                
                # Check if a modal/dialog opened
                modal = await page.query_selector('[role="dialog"], [data-testid*="modal"], .modal, [class*="modal"]')
                if modal:
                    print("🪟 Modal/dialog detected")
                    # Look for input inside modal
                    prompt_input = await modal.query_selector('textarea, input[type="text"]')
                    if prompt_input:
                        print("✅ Found prompt input inside modal")
                        # Use the modal's input
                        print(f"Entering prompt: {prompt}")
                        await prompt_input.fill(f"Generate a video: {prompt}")
                        await asyncio.sleep(1)
                        
                        # Find submit button in modal
                        submit_btn = await modal.query_selector('button[type="submit"], button:has-text("Generate"), button:has-text("Create")')
                        if submit_btn:
                            await submit_btn.click()
                            print("✅ Clicked submit in modal")
                        else:
                            await page.keyboard.press("Enter")
                            print("✅ Pressed Enter to submit")
                        
                        # Jump to waiting for videos
                        return await self._wait_for_videos(page, prompt, num_videos)
                
                # Step 3: Find prompt input on main page
                print("Looking for prompt input...")
                
                # Look for textarea or input
                prompt_input = None
                for selector in [
                    'textarea[data-testid="composer-input"]',
                    'textarea[placeholder*="video" i]',
                    'textarea[placeholder*="ask" i]',
                    'textarea',
                    'input[placeholder*="video" i]',
                ]:
                    try:
                        prompt_input = await page.wait_for_selector(selector, timeout=5000)
                        if prompt_input:
                            print(f"✅ Found prompt input: {selector}")
                            break
                    except:
                        continue
                
                if not prompt_input:
                    return {"success": False, "error": "Could not find prompt input"}
                
                # Fill the prompt
                print(f"Entering prompt: {prompt}")
                await prompt_input.fill(f"Generate a video: {prompt}")
                await asyncio.sleep(1)
                
                # Step 4: Submit
                print("Submitting prompt...")
                await page.keyboard.press("Enter")
                
                # Step 5: Wait for video generation
                return await self._wait_for_videos(page, prompt, num_videos)
                
            except Exception as e:
                await context.close()
                print(f"❌ Error: {e}")
                return {"success": False, "error": str(e)}
    
    async def _wait_for_videos(self, page, prompt: str, num_videos: int) -> dict:
        """Wait for video generation and collect URLs."""
        print("Waiting for video generation (this may take 60-180 seconds)...")
        video_urls = []
        
        for attempt in range(36):  # 3 minutes total
            await asyncio.sleep(5)
            
            # Check for video elements
            videos = await page.query_selector_all('video')
            if videos:
                print(f"🎬 Found {len(videos)} video elements after {(attempt+1)*5}s")
                for vid in videos:
                    src = await vid.get_attribute('src')
                    if src and src not in video_urls:
                        video_urls.append(src)
                        print(f"  Video URL: {src[:70]}...")
                
                if len(video_urls) >= num_videos:
                    break
            
            # Check for video download links
            links = await page.query_selector_all('a[download], a[href*=".mp4"]')
            for link in links:
                href = await link.get_attribute('href')
                if href and href not in video_urls:
                    video_urls.append(href)
                    print(f"  Video link: {href[:70]}...")
            
            # Progress update every 30 seconds
            if (attempt + 1) % 6 == 0:
                elapsed = (attempt + 1) * 5
                print(f"  ⏳ Still waiting... ({elapsed}s elapsed, {len(video_urls)} videos found)")
                await page.screenshot(path=f"debug_video_progress_{elapsed}s.png")
        
        # Final screenshot
        await page.screenshot(path="debug_video_final.png")
        
        return {
            "success": len(video_urls) > 0,
            "prompt": prompt,
            "video_urls": video_urls[:num_videos],
            "count": len(video_urls)
        }
    
    def download(self, url: str, filename: str = None) -> str:
        """Download video from URL."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}_{hash(url) % 10000}.mp4"
        
        filepath = self.downloads_dir / filename
        
        try:
            print(f"⬇️ Downloading from {url[:60]}...")
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
        result = await self.generate(prompt, num_videos)
        
        downloaded = []
        if result.get("success") and result.get("video_urls"):
            for i, url in enumerate(result["video_urls"]):
                filename = f"video_{i+1}_{datetime.now().strftime('%H%M%S')}.mp4"
                filepath = self.download(url, filename)
                if filepath:
                    downloaded.append(filepath)
        
        result["downloaded_files"] = downloaded
        result["download_dir"] = str(self.downloads_dir)
        return result


# Test
if __name__ == "__main__":
    print("="*80)
    print("Meta AI Video Generation Test")
    print("="*80)
    
    generator = VideoGenerator()
    
    result = asyncio.run(generator.generate_and_download(
        prompt="A cat playing piano in a cozy jazz club",
        num_videos=1
    ))
    
    print("\n" + "="*80)
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Prompt: {result.get('prompt')}")
    print(f"  Videos found: {result.get('count')}")
    print(f"  Downloaded: {len(result.get('downloaded_files', []))}")
    for url in result.get('video_urls', []):
        print(f"  URL: {url[:70]}...")
    print("="*80)
