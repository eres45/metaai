"""
Complete Meta AI Generation Service
Supports image generation and video generation (via image animation).
"""
import asyncio
import os
import json
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
        """Load cookies from META_COOKIES env var into browser context."""
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
                await context.add_cookies(playwright_cookies)
                print(f"✅ Loaded {len(playwright_cookies)} cookies into browser")
            except Exception as e:
                print(f"⚠️ Failed to load cookies: {e}")
    
    async def generate_images(
        self, 
        prompt: str, 
        num_images: int = 4
    ) -> Dict:
        """Generate images from text prompt."""
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            # Load storage state from env if available
            storage_json = os.environ.get("STORAGE_STATE")
            if storage_json:
                try:
                    storage_state = json.loads(storage_json)
                    await context.add_cookies(storage_state.get("cookies", []))
                    print(f"✅ Loaded {len(storage_state.get('cookies', []))} cookies from storage state")
                except Exception as e:
                    print(f"⚠️ Failed to load storage state: {e}")
            
            # Navigate to site
            await page.goto("https://www.meta.ai")
            await asyncio.sleep(2)
            
            try:
                print(f"Page loaded: {page.url}")
                
                # Check if logged in
                page_text = await page.evaluate("() => document.body.innerText.slice(0, 500)")
                print(f"Page content preview: {page_text}")
                
                # Submit prompt
                print(f"Submitting prompt: {prompt}")
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
                print("Prompt submitted")
                
                # Wait for generation
                print("Waiting 15s for generation...")
                await asyncio.sleep(15)
                
                # Extract image URLs - look for images from fbcdn (Facebook CDN)
                print("Looking for images...")
                images = await page.query_selector_all('img[src*="fbcdn.net"], img[src*="scontent"], img[data-testid="generated-image"]')
                print(f"Found {len(images)} images")
                image_urls = []
                
                for i, img in enumerate(images[:num_images * 3]):  # Check more images
                    src = await img.get_attribute('src')
                    print(f"Image {i}: {src[:50] if src else 'None'}...")
                    # Filter: must have fbcdn but NOT rsrc.php (logos)
                    if src and src not in image_urls and 'fbcdn' in src and 'rsrc.php' not in src:
                        image_urls.append(src)
                        if len(image_urls) >= num_images:
                            break
                
                await context.close()
                
                return {
                    "success": len(image_urls) > 0,
                    "prompt": prompt,
                    "image_urls": image_urls,
                    "count": len(image_urls)
                }
                
            except Exception as e:
                await context.close()
                return {"success": False, "error": str(e)}
    
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
        """
        Generate video using working Text-to-Video method on /media page.
        Based on Auto Meta extension workflow.
        """
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            try:
                # Load storage state from env if available
                storage_json = os.environ.get("STORAGE_STATE")
                if storage_json:
                    try:
                        storage_state = json.loads(storage_json)
                        await context.add_cookies(storage_state.get("cookies", []))
                        print(f"[VIDEO] ✅ Loaded {len(storage_state.get('cookies', []))} cookies")
                    except Exception as e:
                        print(f"[VIDEO] ⚠️ Cookie load failed: {e}")
                
                # Navigate to /media page
                # Define output_dir early for debug files
                output_dir = self.downloads_dir / "videos"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                print("[VIDEO] Navigating to main Meta AI...")
                await page.goto("https://www.meta.ai/")
                await asyncio.sleep(3)
                
                # Look for and click "New chat" or similar to start fresh
                print("[VIDEO] Starting new chat...")
                await page.evaluate("""() => {
                    // Try to find new chat button
                    const newChatBtn = Array.from(document.querySelectorAll('button, a')).find(
                        el => el.textContent && el.textContent.toLowerCase().includes('new chat')
                    );
                    if (newChatBtn) {
                        newChatBtn.click();
                        return true;
                    }
                    return false;
                }""")
                await asyncio.sleep(2)
                
                print(f"[VIDEO] Page loaded: {page.url}")
                
                # Enter prompt
                print(f"[VIDEO] Entering prompt: {prompt}")
                await page.evaluate("""(prompt) => {
                    const ta = document.querySelector('textarea[data-testid="composer-input"]');
                    if (ta) {
                        ta.value = prompt;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", prompt)
                await asyncio.sleep(1)
                
                # Submit
                print("[VIDEO] Submitting...")
                await page.keyboard.press("Enter")
                await asyncio.sleep(5)
                
                # DEBUG: Check what happened after submit
                page_text = await page.evaluate("() => document.body.innerText.slice(0, 800)")
                print(f"[VIDEO] Page after submit: {page_text[:200]}...")
                print(f"[VIDEO] URL after submit: {page.url}")
                
                # Check if we see any generation indicators
                has_generating = await page.evaluate("""() => {
                    const text = document.body.innerText.toLowerCase();
                    return text.includes('generating') || text.includes('creating') || text.includes('animate');
                }""")
                print(f"[VIDEO] Generation indicators found: {has_generating}")
                
                # DEBUG: Take screenshot and check page content
                await page.screenshot(path=str(output_dir / "debug_after_submit.png"))
                print(f"[VIDEO] Screenshot saved")
                
                # Check what's on the page
                page_text_check = await page.evaluate("""() => {
                    const text = document.body.innerText;
                    // Look for video-related terms
                    return {
                        hasVideo: text.includes('video') || text.includes('Video'),
                        hasDancing: text.includes('Dancing'),
                        textPreview: text.slice(0, 500)
                    };
                }""")
                print(f"[VIDEO] Page check: {page_text_check}")
                
                # Wait for videos - poll every 3s for 90s
                print("[VIDEO] Waiting for videos (up to 90s)...")
                video_urls = []
                
                for i in range(30):  # 90 seconds
                    await asyncio.sleep(3)
                    elapsed = (i + 1) * 3
                    
                    # Get page HTML for source analysis
                    page_html = await page.content()
                    
                    # Search for fbcdn video URLs in page source (most reliable)
                    import re
                    # Look for all fbcdn.net URLs with video
                    fbcdn_pattern = r'https://[^"\s<>]+fbcdn\.net[^"\s<>]*\.mp4[^"\s<>]*'
                    matches = re.findall(fbcdn_pattern, page_html)
                    
                    if matches and i % 5 == 0:  # Log every 15s if matches found
                        print(f"[VIDEO] [{elapsed}s] Raw matches: {len(matches)}")
                    
                    for url in matches:
                        # Clean up URL (handle escaped characters)
                        clean_url = url.replace('\\u0026', '&').replace('\\', '').replace('&amp;', '&')
                        if clean_url not in video_urls and 'fbcdn.net' in clean_url:
                            video_urls.append(clean_url)
                            print(f"[VIDEO] [{elapsed}s] Found URL: {clean_url[:80]}...")
                    
                    if len(video_urls) >= 4:
                        print(f"[VIDEO] Got {len(video_urls)} URLs, breaking early")
                        break
                    
                    # Also check for video elements
                    videos = await page.query_selector_all('video')
                    if videos:
                        print(f"[VIDEO] [{elapsed}s] Found {len(videos)} video elements")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls:
                                video_urls.append(src)
                                print(f"[VIDEO]   Video src: {src[:60]}...")
                    
                    # Progress update every 15s
                    if elapsed % 15 == 0 and len(video_urls) < 4:
                        # Count "Dancing" or prompt words in page to see if generating
                        page_text = await page.evaluate("() => document.body.innerText")
                        prompt_words = prompt.lower().split()[:2]  # First 2 words of prompt
                        found_words = sum(1 for w in prompt_words if w in page_text.lower())
                        print(f"[VIDEO] [{elapsed}s] Waiting... (found {len(video_urls)} URLs, {found_words}/{len(prompt_words)} prompt words in page)")
                
                # Final check: look for video URLs in page source
                if len(video_urls) < 4:
                    print(f"[VIDEO] Final check: searching page source... (have {len(video_urls)})")
                    page_html = await page.content()
                    
                    # DEBUG: Save HTML for analysis
                    debug_html_path = output_dir / "debug_page.html"
                    with open(debug_html_path, 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    print(f"[VIDEO] Saved HTML to {debug_html_path}")
                    
                    import re
                    # Look for all https URLs containing video or mp4
                    all_urls = re.findall(r'https://[^"\s<>]+', page_html)
                    video_urls_found = [u for u in all_urls if 'video' in u.lower() or '.mp4' in u.lower()]
                    print(f"[VIDEO] All video-like URLs found: {len(video_urls_found)}")
                    for i, url in enumerate(video_urls_found[:10]):
                        print(f"[VIDEO]   {i+1}: {url[:100]}...")
                
                # Download videos by navigating to URL and return base64
                video_data_list = []
                if video_urls:
                    print(f"[VIDEO] Downloading {len(video_urls)} videos via base64...")
                    
                    for i, url in enumerate(video_urls[:4]):
                        try:
                            print(f"[VIDEO] Downloading video {i+1}...")
                            
                            # Navigate to video URL
                            await page.goto(url, wait_until="networkidle", timeout=60000)
                            
                            # Get video element and download via fetch
                            video_base64 = await page.evaluate("""async () => {
                                const video = document.querySelector('video');
                                if (!video || !video.src) return null;
                                
                                try {
                                    const response = await fetch(video.src);
                                    const blob = await response.blob();
                                    return new Promise((resolve) => {
                                        const reader = new FileReader();
                                        reader.onloadend = () => resolve(reader.result);
                                        reader.readAsDataURL(blob);
                                    });
                                } catch (e) {
                                    return null;
                                }
                            }""")
                            
                            if video_base64:
                                # Remove data:video/mp4;base64, prefix
                                base64_data = video_base64.split(',')[1] if ',' in video_base64 else video_base64
                                video_data_list.append({
                                    "index": i + 1,
                                    "base64": base64_data,
                                    "size": len(base64_data)
                                })
                                print(f"[VIDEO] ✅ Video {i+1} encoded ({len(base64_data):,} chars)")
                            else:
                                print(f"[VIDEO] ❌ Video {i+1} failed to encode")
                                
                        except Exception as e:
                            print(f"[VIDEO] ❌ Video {i+1} error: {e}")
                
                await context.close()
                
                print(f"[VIDEO] Complete: {len(video_urls)} videos found, {len(video_data_list)} encoded")
                return {
                    "success": len(video_urls) > 0,
                    "prompt": prompt,
                    "video_urls": video_urls[:4],
                    "videos_base64": video_data_list,
                    "download_instruction": "Decode base64: echo 'BASE64_DATA' | base64 -d > video.mp4",
                    "count": len(video_urls)
                }
                
            except Exception as e:
                print(f"[VIDEO] Error: {e}")
                await context.close()
                return {"success": False, "error": str(e)}
    
    async def generate_and_download_video_v2(self, prompt: str) -> Dict:
        """Generate video using v2 method and download."""
        result = await self.generate_video_v2(prompt)
        
        output_dir = self.downloads_dir / "videos"
        downloaded = []
        
        if result.get("success") and result.get("video_urls"):
            for i, url in enumerate(result["video_urls"]):
                filename = f"video_{i+1}.mp4"
                filepath = self.download_file(url, output_dir, filename)
                if filepath:
                    downloaded.append(filepath)
        
        result["downloaded_files"] = downloaded
        result["download_dir"] = str(output_dir)
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
