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
        print(f"[IMAGES] ========== STARTING IMAGE GENERATION ==========")
        print(f"[IMAGES] Prompt: {prompt}, Num: {num_images}")
        
        async with async_playwright() as p:
            try:
                print(f"[IMAGES] Step 1: Launching browser...")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
                )
                print(f"[IMAGES] Step 1: ✅ Browser launched")
            except Exception as e:
                print(f"[IMAGES] Step 1: ❌ Browser launch failed: {e}")
                return {"success": False, "error": f"Browser launch failed: {e}"}
            
            page = await context.new_page()
            print(f"[IMAGES] Step 2: Page created")
            
            # Load cookies from env
            print(f"[IMAGES] Step 3: Loading cookies...")
            cookies_loaded = await self._setup_cookies_from_env(context)
            print(f"[IMAGES] Step 3: Cookies loaded: {cookies_loaded}")
            
            # Navigate to site
            try:
                print("[IMAGES] Step 4: Navigating to meta.ai...")
                await page.goto("https://www.meta.ai", timeout=20000)
                await asyncio.sleep(2)
                print(f"[IMAGES] Step 4: ✅ Navigated to {page.url}")
            except Exception as e:
                print(f"[IMAGES] Step 4: ❌ Navigation failed: {e}")
                await context.close()
                return {"success": False, "error": f"Navigation failed: {e}"}
            
            try:
                print(f"[IMAGES] Step 5: Checking page content...")
                page_text = await page.evaluate("() => document.body.innerText.slice(0, 500)")
                print(f"[IMAGES] Step 5: Page content preview: {page_text[:100]}...")
                
                # Submit prompt
                print(f"[IMAGES] Step 6: Submitting prompt...")
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
                print("[IMAGES] Step 6: ✅ Prompt submitted")
                
                # Wait for generation with HTML polling
                print("[IMAGES] Step 7: Polling for images (max 45s, checking every 3s)...")
                max_wait = 45
                check_interval = 3
                min_wait = 10
                
                await asyncio.sleep(min_wait)
                elapsed = min_wait
                print(f"[IMAGES] Step 7: Initial wait of {min_wait}s complete")
                
                image_urls = []
                poll_count = 0
                
                while elapsed < max_wait:
                    poll_count += 1
                    print(f"[IMAGES] Poll #{poll_count} at {elapsed}s...")
                    
                    # Check for images in HTML
                    page_html = await page.content()
                    html_length = len(page_html)
                    print(f"[IMAGES] HTML length: {html_length} chars")
                    
                    # Multiple patterns
                    patterns = [
                        r'https://scontent[^"\s]*?fbcdn\.net[^"\s]*?\.(?:jpeg|jpg|png|webp)[^"\s]*',
                        r'https://[^"\s]*?fbcdn\.net[^"\s]*?/o1/v/t0[^"\s]*?\.(?:jpeg|jpg|png|webp)[^"\s]*',
                        r'https://[^"\s]*?\.fbcdn\.net[^"\s]*?\.(?:jpeg|jpg|png|webp)[^"\s]*',
                    ]
                    
                    for idx, pattern in enumerate(patterns):
                        fbcdn_matches = re.findall(pattern, page_html)
                        if fbcdn_matches:
                            print(f"[IMAGES] Pattern {idx+1} found {len(fbcdn_matches)} URLs")
                            for url in fbcdn_matches[:5]:  # Show first 5
                                clean_url = url.replace('&amp;', '&')
                                print(f"[IMAGES]   Checking: {clean_url[:120]}...")
                                
                                if clean_url not in image_urls and 'rsrc.php' not in clean_url:
                                    image_urls.append(clean_url)
                                    print(f"[IMAGES]   ✅ ADDED to results!")
                                    if len(image_urls) >= num_images:
                                        break
                                elif 'rsrc.php' in clean_url:
                                    print(f"[IMAGES]   ❌ Skipped (rsrc.php - logo)")
                                else:
                                    print(f"[IMAGES]   ⚠️ Skipped (duplicate)")
                        if len(image_urls) >= num_images:
                            break
                    
                    if len(image_urls) >= num_images:
                        print(f"[IMAGES] ✅ Found {num_images}+ images at {elapsed}s, exiting!")
                        break
                    
                    print(f"[IMAGES] Current count: {len(image_urls)}/{num_images}")
                    
                    await asyncio.sleep(check_interval)
                    elapsed += check_interval
                
                print(f"[IMAGES] Step 7: ✅ Polling complete. Found {len(image_urls)} images")
                
                # Final check
                print("[IMAGES] Step 8: Final extraction check...")
                if not image_urls:
                    print("[IMAGES] No images found, doing aggressive final check...")
                    page_html = await page.content()
                    
                    for idx, pattern in enumerate(patterns):
                        matches = re.findall(pattern, page_html)
                        if matches:
                            print(f"[IMAGES] Final pattern {idx+1} found {len(matches)} URLs")
                            for url in matches[:10]:
                                clean_url = url.replace('&amp;', '&')
                                if clean_url not in image_urls and 'rsrc.php' not in clean_url:
                                    image_urls.append(clean_url)
                                    print(f"[IMAGES] Final added: {clean_url[:100]}...")
                                    if len(image_urls) >= num_images:
                                        break
                        if len(image_urls) >= num_images:
                            break
                
                print(f"[IMAGES] Step 8: ✅ Final count: {len(image_urls)} images")
                
                await context.close()
                print(f"[IMAGES] Step 9: ✅ Browser closed")
                
                result = {
                    "success": len(image_urls) > 0,
                    "prompt": prompt,
                    "image_urls": image_urls[:num_images],
                    "count": len(image_urls),
                    "cookies_loaded": cookies_loaded
                }
                print(f"[IMAGES] ========== RESULT: {result['success']} ({result['count']} images) ==========")
                return result
                
            except Exception as e:
                print(f"[IMAGES] ❌ ERROR during generation: {e}")
                import traceback
                print(f"[IMAGES] Traceback: {traceback.format_exc()}")
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
                    page_html = await page.content()
                    
                    # Multiple patterns to catch all possible video URLs
                    patterns = [
                        r'https://[^"\s]*?\.mp4[^"\s]*',
                        r'https://video[^"\s]*?fbcdn\.net[^"\s]*?\.mp4[^"\s]*',
                        r'https://[^"\s]*?fbcdn\.net[^"\s]*?/o1/v/t[^"\s]*?\.mp4[^"\s]*',
                    ]
                    
                    for pattern in patterns:
                        mp4_matches = re.findall(pattern, page_html)
                        if mp4_matches:
                            print(f"[VIDEO] [{elapsed}s] Found {len(mp4_matches)} .mp4 URLs with pattern")
                            for url in mp4_matches:
                                clean_url = url.replace('&amp;', '&')
                                if clean_url not in video_urls:
                                    video_urls.append(clean_url)
                                    print(f"[VIDEO] Added: {clean_url[:80]}...")
                            if len(video_urls) >= 4:
                                break
                    
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
