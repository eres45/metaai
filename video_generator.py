"""
Navigate to Meta AI Create video section and generate video.
"""
import asyncio
from playwright.async_api import async_playwright
import os
import requests
from pathlib import Path
from datetime import datetime


class MetaVideoGenerator:
    """Video generation via Meta AI Create section."""
    
    def __init__(self, user_data_dir: str = "./meta_session"):
        self.user_data_dir = user_data_dir
        self.downloads_dir = Path("downloads/videos")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_video(self, prompt: str, num_videos: int = 1) -> dict:
        """
        Generate video using Meta AI Create section.
        
        Args:
            prompt: Video description
            num_videos: Number of videos to generate
        
        Returns:
            Dict with success status and video URLs
        """
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            try:
                # Navigate directly to media page
                print("Navigating to Meta AI media page...")
                await page.goto("https://www.meta.ai/media")
                await asyncio.sleep(5)
                
                # Look for and click "Create video" button
                print("Looking for Create video button...")
                
                # Try different selectors for Create video
                create_selectors = [
                    'button:has-text("Create video")',
                    '[data-testid] button:has-text("Create video")',
                    'a:has-text("Create video")',
                ]
                
                clicked = False
                for selector in create_selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=5000)
                        if btn:
                            await btn.click()
                            print(f"Clicked Create video with: {selector}")
                            clicked = True
                            await asyncio.sleep(3)
                            break
                    except:
                        continue
                
                if not clicked:
                    # Try JavaScript click
                    result = await page.evaluate("""() => {
                        const buttons = Array.from(document.querySelectorAll('button, a'));
                        const btn = buttons.find(b => b.textContent && b.textContent.includes('Create video'));
                        if (btn) {
                            btn.click();
                            return 'clicked';
                        }
                        return 'not-found';
                    }""")
                    print(f"JS click result: {result}")
                    if result == 'clicked':
                        clicked = True
                        await asyncio.sleep(3)
                
                if not clicked:
                    print("Could not find Create video button")
                    return {"success": False, "error": "Create video button not found"}
                
                print(f"Current URL after click: {page.url}")
                await page.screenshot(path="debug_after_create_video.png")
                
                # Now look for prompt input
                print("Looking for prompt input...")
                
                # Try to find the prompt textarea
                prompt_selectors = [
                    'textarea[placeholder*="video" i]',
                    'textarea[placeholder*="describe" i]',
                    'textarea[data-testid*="input" i]',
                    'textarea',
                    'input[placeholder*="video" i]',
                ]
                
                prompt_input = None
                for selector in prompt_selectors:
                    try:
                        prompt_input = await page.wait_for_selector(selector, timeout=5000)
                        if prompt_input:
                            print(f"Found prompt input: {selector}")
                            break
                    except:
                        continue
                
                if not prompt_input:
                    # Try JavaScript to find input
                    result = await page.evaluate("""() => {
                        const inputs = Array.from(document.querySelectorAll('textarea, input[type="text"]'));
                        const input = inputs.find(i => {
                            const ph = i.getAttribute('placeholder') || '';
                            return ph.toLowerCase().includes('video') || ph.toLowerCase().includes('describe');
                        });
                        if (input) return 'found-input';
                        if (inputs.length > 0) return `found-${inputs.length}-inputs`;
                        return 'no-inputs';
                    }""")
                    print(f"Input search result: {result}")
                    return {"success": False, "error": "Prompt input not found"}
                
                # Fill the prompt
                print(f"Filling prompt: {prompt}")
                await prompt_input.fill(prompt)
                await asyncio.sleep(1)
                
                # Look for generate button
                print("Looking for generate button...")
                generate_selectors = [
                    'button:has-text("Generate")',
                    'button[type="submit"]',
                    'button:has-text("Create")',
                ]
                
                generate_btn = None
                for selector in generate_selectors:
                    try:
                        generate_btn = await page.wait_for_selector(selector, timeout=5000)
                        if generate_btn:
                            break
                    except:
                        continue
                
                if generate_btn:
                    await generate_btn.click()
                    print("Clicked generate button")
                else:
                    # Press Enter
                    await page.keyboard.press("Enter")
                    print("Pressed Enter to submit")
                
                # Wait for video generation
                print("Waiting for video generation (this may take 60-120 seconds)...")
                video_urls = []
                
                for attempt in range(24):  # 2 minutes total
                    await asyncio.sleep(5)
                    
                    # Check for video elements
                    videos = await page.query_selector_all('video')
                    if videos:
                        print(f"Found {len(videos)} video elements after {(attempt+1)*5}s")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls:
                                video_urls.append(src)
                        
                        if len(video_urls) >= num_videos:
                            break
                    
                    # Also check for download links
                    links = await page.query_selector_all('a[download], a[href*=".mp4"]')
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and href not in video_urls:
                            video_urls.append(href)
                
                await page.screenshot(path="debug_final_video.png")
                
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
    
    async def generate_and_download(
        self,
        prompt: str,
        num_videos: int = 1
    ) -> dict:
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
    print("Meta AI Video Generation Test")
    print("="*80)
    
    generator = MetaVideoGenerator()
    
    result = asyncio.run(generator.generate_and_download(
        prompt="A cat playing piano in a jazz club",
        num_videos=1
    ))
    
    print("\n" + "="*80)
    print("Result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Video URLs: {len(result.get('video_urls', []))}")
    print(f"  Downloaded: {len(result.get('downloaded_files', []))}")
    for url in result.get('video_urls', []):
        print(f"    - {url[:80]}...")
    print("="*80)
