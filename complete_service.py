"""
Complete Meta AI Generation Service
Supports image generation and video generation (via image animation).
"""
import asyncio
import os
import json
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from playwright.async_api import async_playwright


class MetaGenerationService:
    """Complete generation service for Meta AI."""
    
    def __init__(self, user_data_dir: str = "./meta_session"):
        self.user_data_dir = user_data_dir
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
    
    async def _setup_cookies_from_env(self, context):
        """Load cookies from META_COOKIES or STORAGE_STATE env var into browser context."""
        
        # Try STORAGE_STATE first (full storage state format)
        storage_json = os.environ.get("STORAGE_STATE")
        if storage_json:
            try:
                storage_state = json.loads(storage_json)
                cookies = storage_state.get("cookies", [])
                if cookies:
                    await context.add_cookies(cookies)
                    print(f"✅ Loaded {len(cookies)} cookies from STORAGE_STATE")
                    return True
            except Exception as e:
                print(f"⚠️ Failed to load STORAGE_STATE: {e}")
        
        # Fallback to META_COOKIES (simple dict format)
        cookies_json = os.environ.get("META_COOKIES")
        if cookies_json:
            try:
                cookies_dict = json.loads(cookies_json)
                # Convert to Playwright cookie format
                playwright_cookies = []
                for name, value in cookies_dict.items():
                    playwright_cookies.append({
                        "name": name,
                        "value": value,
                        "domain": ".meta.ai",
                        "path": "/",
                        "secure": True,
                        "httpOnly": True
                    })
                if playwright_cookies:
                    await context.add_cookies(playwright_cookies)
                    print(f"✅ Loaded {len(playwright_cookies)} cookies from META_COOKIES")
                    return True
            except Exception as e:
                print(f"⚠️ Failed to load META_COOKIES: {e}")
        
        print("⚠️ No valid cookies found in environment")
        return False
    
    async def generate_images(
        self, 
        prompt: str, 
        num_images: int = 4
    ) -> Dict:
        """Generate images from text prompt."""
        print(f"[IMAGES] Starting generation for: {prompt}")
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
            except Exception as e:
                print(f"[IMAGES] Failed to launch browser: {e}")
                return {"success": False, "error": f"Browser launch failed: {e}"}
            
            page = await context.new_page()
            
            # Load cookies from env
            cookies_loaded = await self._setup_cookies_from_env(context)
            if not cookies_loaded:
                print("[IMAGES] Warning: No cookies loaded, may need login")
            
            # Navigate to site
            try:
                print("[IMAGES] Navigating to meta.ai...")
                await page.goto("https://www.meta.ai", timeout=30000)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[IMAGES] Failed to navigate: {e}")
                await context.close()
                return {"success": False, "error": f"Navigation failed: {e}"}
            
            try:
                print(f"[IMAGES] Page loaded: {page.url}")
                
                # Check if logged in
                page_text = await page.evaluate("() => document.body.innerText.slice(0, 500)")
                print(f"[IMAGES] Page content: {page_text[:200]}...")
                
                # Submit prompt
                print(f"[IMAGES] Submitting prompt: {prompt}")
                await page.evaluate("""(prompt) => {
                    const textarea = document.querySelector('textarea[data-testid="composer-input"]');
                    if (textarea) {
                        textarea.value = prompt;
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        console.log('Prompt set');
                    } else {
                        console.log('Textarea not found');
                    }
                }""", prompt)
                await page.keyboard.press("Enter")
                print("[IMAGES] Prompt submitted")
                
                # Wait for generation with polling
                print("[IMAGES] Waiting for generation (max 30s)...")
                max_wait = 30
                check_interval = 3
                elapsed = 0
                
                while elapsed < max_wait:
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
                    
                    # Check if images appeared
                    images = await page.query_selector_all('img[src*="fbcdn.net"]')
                    fbcdn_count = 0
                    for img in images:
                        src = await img.get_attribute('src')
                        if src and 'rsrc.php' not in src:
                            fbcdn_count += 1
                    
                    if fbcdn_count >= num_images:
                        print(f"[IMAGES] Found {fbcdn_count} images after {elapsed}s")
                        break
                    
                    if elapsed % 9 == 0:
                        print(f"[IMAGES] Still waiting... ({elapsed}s, found {fbcdn_count} images)")
                
                print(f"[IMAGES] Finished waiting after {elapsed}s")
                
                # Extract image URLs - look for images from fbcdn (Facebook CDN)
                print("[IMAGES] Looking for images...")
                
                # Try simple selector first (like debug endpoint)
                images = await page.query_selector_all('img[src*="fbcdn.net"]')
                print(f"[IMAGES] Found {len(images)} images with simple selector")
                
                image_urls = []
                for i, img in enumerate(images[:num_images * 3]):
                    src = await img.get_attribute('src')
                    if src:
                        print(f"[IMAGES] Image {i}: {src[:60] if src else 'None'}...")
                    # Filter out rsrc.php (logos) and scontent (generated images)
                    if src and src not in image_urls and 'rsrc.php' not in src and 'scontent' in src:
                        image_urls.append(src)
                        if len(image_urls) >= num_images:
                            break
                
                # Fallback: extract from HTML if no images found
                if not image_urls:
                    print("[IMAGES] No images from selector, trying HTML extraction...")
                    page_html = await page.content()
                    import re
                    # Look for scontent fbcdn URLs (the generated images)
                    fbcdn_urls = re.findall(r'https://scontent[^"\s]*fbcdn\.net[^"\s]*\.(?:jpeg|jpg|png)[^"\s]*', page_html)
                    print(f"[IMAGES] Found {len(fbcdn_urls)} URLs in HTML")
                    for url in fbcdn_urls:
                        clean_url = url.replace('&amp;', '&')
                        if clean_url not in image_urls:
                            image_urls.append(clean_url)
                            print(f"[IMAGES] URL from HTML: {clean_url[:60]}...")
                        if len(image_urls) >= num_images:
                            break
                
                await context.close()
                
                result = {
                    "success": len(image_urls) > 0,
                    "prompt": prompt,
                    "image_urls": image_urls,
                    "count": len(image_urls),
                    "cookies_loaded": cookies_loaded
                }
                print(f"[IMAGES] Result: {result}")
                return result
                
            except Exception as e:
                print(f"[IMAGES] Error during generation: {e}")
                await context.close()
                return {"success": False, "error": str(e), "cookies_loaded": cookies_loaded}
    
    async def generate_video(
        self, 
        prompt: str,
        animate_index: int = 0
    ) -> Dict:
        """
        Generate video by creating images and animating one.
        
        Args:
            prompt: Video description
            animate_index: Which image to animate (0-3)
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
                print(f"Generating images for: {prompt}")
                await page.goto("https://www.meta.ai")
                
                await page.evaluate("""(prompt) => {
                    const ta = document.querySelector('textarea[data-testid="composer-input"]');
                    if (ta) {
                        ta.value = prompt;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", prompt)
                await page.keyboard.press("Enter")
                
                # Wait for images
                await asyncio.sleep(15)
                
                # Step 2: Click on image to view
                view_links = await page.query_selector_all('a[aria-label="View media"]')
                if not view_links or animate_index >= len(view_links):
                    return {"success": False, "error": "No images to animate"}
                
                print(f"Clicking image {animate_index} to view...")
                await view_links[animate_index].click()
                await asyncio.sleep(3)
                
                # Step 3: Click Animate button
                print("Clicking Animate button...")
                result = await page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const animateBtn = btns.find(b => 
                        b.textContent && b.textContent.trim() === 'Animate');
                    if (animateBtn) {
                        animateBtn.click();
                        return 'clicked';
                    }
                    return 'not-found';
                }""")
                
                if result != 'clicked':
                    return {"success": False, "error": "Could not click Animate button"}
                
                print("Waiting for video generation (60-120 seconds)...")
                video_urls = []
                
                for attempt in range(24):  # 2 minutes
                    await asyncio.sleep(5)
                    
                    # Check for video
                    videos = await page.query_selector_all('video')
                    if videos:
                        print(f"Found {len(videos)} videos after {(attempt+1)*5}s")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls:
                                video_urls.append(src)
                        
                        if len(video_urls) > 0:
                            break
                    
                    if (attempt + 1) % 6 == 0:
                        print(f"  Still waiting... ({(attempt+1)*5}s elapsed)")
                
                await context.close()
                
                return {
                    "success": len(video_urls) > 0,
                    "prompt": prompt,
                    "video_urls": video_urls,
                    "count": len(video_urls)
                }
                
            except Exception as e:
                await context.close()
                return {"success": False, "error": str(e)}
    
    def download_file(
        self, 
        url: str, 
        output_dir: Path,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """Download file from URL."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = '.mp4' if '.mp4' in url else '.jpg'
            filename = f"meta_{timestamp}_{hash(url) % 10000}{ext}"
        
        filepath = output_dir / filename
        
        try:
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(filepath)
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    async def generate_and_download_images(
        self,
        prompt: str,
        num_images: int = 4
    ) -> Dict:
        """Generate images and download them."""
        result = await self.generate_images(prompt, num_images)
        
        output_dir = self.downloads_dir / "images"
        downloaded = []
        
        if result.get("success") and result.get("image_urls"):
            for i, url in enumerate(result["image_urls"]):
                filename = f"image_{i+1}.jpg"
                filepath = self.download_file(url, output_dir, filename)
                if filepath:
                    downloaded.append(filepath)
        
        result["downloaded_files"] = downloaded
        result["download_dir"] = str(output_dir)
        return result
    
    async def generate_video_v2(self, prompt: str) -> Dict:
        """Generate video using main Meta AI chat with 'Generate a video:' prefix."""
        print(f"[VIDEO] Starting generation for: {prompt}")
        async with async_playwright() as p:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
            except Exception as e:
                print(f"[VIDEO] Failed to launch browser: {e}")
                return {"success": False, "error": f"Browser launch failed: {e}"}
            
            page = await context.new_page()
            
            # Load cookies from env
            cookies_loaded = await self._setup_cookies_from_env(context)
            if not cookies_loaded:
                print("[VIDEO] Warning: No cookies loaded, may need login")
            
            try:
                # Navigate to main Meta AI page
                print("[VIDEO] Navigating to main Meta AI...")
                await page.goto("https://www.meta.ai/", timeout=30000)
                await asyncio.sleep(3)
                print(f"[VIDEO] Page: {page.url}")
                
                # Use video generation prefix
                video_prompt = f"Generate a video: {prompt}"
                print(f"[VIDEO] Entering: {video_prompt}")
                await page.evaluate("""(prompt) => {
                    const ta = document.querySelector('textarea[data-testid="composer-input"]');
                    if (ta) {
                        ta.value = prompt;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    } else {
                        console.log('[VIDEO] Textarea not found!');
                    }
                }""", video_prompt)
                await asyncio.sleep(1)
                
                print("[VIDEO] Submitting...")
                await page.keyboard.press("Enter")
                await asyncio.sleep(10)
                
                print(f"[VIDEO] URL after submit: {page.url}")
                
                # Wait for videos - check page content for generation status
                print("[VIDEO] Waiting for videos (90s max)...")
                video_urls = []
                page_checked = False
                
                for i in range(30):
                    await asyncio.sleep(3)
                    elapsed = (i + 1) * 3
                    
                    # Check 1: Look for video elements
                    videos = await page.query_selector_all('video')
                    if videos:
                        print(f"[VIDEO] [{elapsed}s] Found {len(videos)} video elements")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls and '.mp4' in src:
                                video_urls.append(src)
                                print(f"[VIDEO] URL from element: {src[:60]}...")
                    
                    # Check 2: Look for video containers/links
                    video_links = await page.query_selector_all('a[href*="video"], a[href*="fbcdn"]')
                    if video_links:
                        print(f"[VIDEO] [{elapsed}s] Found {len(video_links)} video links")
                        for link in video_links:
                            href = await link.get_attribute('href')
                            if href and href not in video_urls and '.mp4' in href:
                                video_urls.append(href)
                                print(f"[VIDEO] URL from link: {href[:60]}...")
                    
                    # Check 3: Extract from HTML (most reliable for Meta AI)
                    if not video_urls or elapsed % 10 == 0:
                        page_html = await page.content()
                        
                        # Use the pattern that worked in debug
                        mp4_matches = re.findall(r'https://[^"\s<>]*\.mp4[^"\s<>]*', page_html)
                        
                        if mp4_matches:
                            print(f"[VIDEO] [{elapsed}s] Found {len(mp4_matches)} .mp4 URLs in HTML")
                            for url in mp4_matches:
                                clean_url = url.replace('&amp;', '&')
                                if clean_url not in video_urls:
                                    video_urls.append(clean_url)
                                    print(f"[VIDEO] URL: {clean_url[:60]}...")
                        
                        # Also try fbcdn specific pattern as fallback
                        fbcdn_matches = re.findall(r'https://[^"\s<>]*fbcdn\.net[^"\s<>]*\.mp4[^"\s<>]*', page_html)
                        if fbcdn_matches:
                            print(f"[VIDEO] [{elapsed}s] Found {len(fbcdn_matches)} fbcdn URLs")
                            for url in fbcdn_matches:
                                clean_url = url.replace('&amp;', '&')
                                if clean_url not in video_urls:
                                    video_urls.append(clean_url)
                                    print(f"[VIDEO] fbcdn URL: {clean_url[:60]}...")
                    
                    if len(video_urls) >= 4:
                        print(f"[VIDEO] Found {len(video_urls)} videos, stopping")
                        break
                    
                    if elapsed % 15 == 0 and not video_urls:
                        print(f"[VIDEO] [{elapsed}s] Still waiting for videos...")
                
                await context.close()
                
                print(f"[VIDEO] Complete: {len(video_urls)} videos found")
                return {
                    "success": len(video_urls) > 0,
                    "prompt": prompt,
                    "video_urls": video_urls[:4],
                    "count": len(video_urls),
                    "cookies_loaded": cookies_loaded
                }
                
            except Exception as e:
                print(f"[VIDEO] Error: {e}")
                await context.close()
                return {"success": False, "error": str(e), "cookies_loaded": cookies_loaded}
    
    async def download_video_with_browser(self, video_url: str, output_path: str) -> bool:
        """Download video using browser fetch with session cookies."""
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            try:
                storage_json = os.environ.get("STORAGE_STATE")
                if storage_json:
                    try:
                        storage_state = json.loads(storage_json)
                        await context.add_cookies(storage_state.get("cookies", []))
                    except:
                        pass
                
                page = await context.new_page()
                
                result = await page.evaluate("""async (url) => {
                    try {
                        const response = await fetch(url);
                        if (!response.ok) return null;
                        const blob = await response.blob();
                        return new Promise((resolve) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    } catch (e) {
                        return null;
                    }
                }""", video_url)
                
                await context.close()
                
                if result:
                    base64_data = result.split(',')[1] if ',' in result else result
                    import base64
                    video_bytes = base64.b64decode(base64_data)
                    with open(output_path, 'wb') as f:
                        f.write(video_bytes)
                    return True
                
                return False
                
            except Exception as e:
                print(f"Browser download failed: {e}")
                await context.close()
                return False
    
    async def generate_and_download_video_v2(self, prompt: str) -> Dict:
        """Generate video and return URLs (download happens client-side with cookies)."""
        result = await self.generate_video_v2(prompt)
        
        # Skip slow server-side download, just return URLs
        # Client should use download_helper.py with cookies
        result["download_dir"] = str(self.downloads_dir / "videos")
        result["note"] = "Use download_helper.py with STORAGE_STATE env to download videos"
        
        return result


# Singleton
_service = None

def get_service():
    global _service
    if _service is None:
        _service = MetaGenerationService()
    return _service


# Test
if __name__ == "__main__":
    print("="*80)
    print("Meta AI Generation Service Test")
    print("="*80)
    
    service = get_service()
    
    # Test images
    print("\n[1] Testing Image Generation")
    print("-"*80)
    img_result = asyncio.run(service.generate_and_download_images(
        prompt="A serene mountain landscape at sunset",
        num_images=2
    ))
    print(f"Images: {img_result.get('count')} generated, {len(img_result.get('downloaded_files', []))} downloaded")
    
    # Test video
    print("\n[2] Testing Video Generation")
    print("-"*80)
    vid_result = asyncio.run(service.generate_and_download_video(
        prompt="A cat playing piano",
        animate_index=0
    ))
    print(f"Video: {vid_result.get('success')}, {len(vid_result.get('video_urls', []))} URLs")
    
    print("\n" + "="*80)
    print("Test complete!")
    print("="*80)
