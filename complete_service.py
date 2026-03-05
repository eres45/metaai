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
        
        # Load cookies from environment variable if available
        self._setup_cookies_from_env()
    
    def _setup_cookies_from_env(self):
        """Load cookies from META_COOKIES env var and save to session."""
        cookies_json = os.environ.get("META_COOKIES")
        if cookies_json:
            try:
                cookies = json.loads(cookies_json)
                self._save_cookies_to_session(cookies)
                print(f"✅ Loaded {len(cookies)} cookies from environment")
            except Exception as e:
                print(f"⚠️ Failed to load cookies from env: {e}")
    
    def _save_cookies_to_session(self, cookies: dict):
        """Save cookies to the Chrome session SQLite database."""
        import sqlite3
        
        session_path = Path(self.user_data_dir) / "Default"
        session_path.mkdir(parents=True, exist_ok=True)
        
        cookies_db = session_path / "Cookies"
        
        # Create/connect to SQLite database
        conn = sqlite3.connect(str(cookies_db))
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                creation_utc INTEGER,
                host_key TEXT,
                name TEXT,
                value TEXT,
                path TEXT,
                expires_utc INTEGER,
                is_secure INTEGER,
                is_httponly INTEGER,
                last_access_utc INTEGER,
                has_expires INTEGER,
                is_persistent INTEGER,
                priority INTEGER,
                encrypted_value BLOB,
                samesite INTEGER,
                source_scheme INTEGER,
                source_port INTEGER,
                is_same_party INTEGER
            )
        """)
        
        # Insert cookies
        from time import time
        now = int(time() * 1000000)
        
        for name, value in cookies.items():
            cursor.execute("""
                INSERT OR REPLACE INTO cookies 
                (creation_utc, host_key, name, value, path, expires_utc, is_secure, is_httponly, last_access_utc, has_expires, is_persistent, priority)
                VALUES (?, '.meta.ai', ?, ?, '/', 0, 1, 1, ?, 0, 1, 1)
            """, (now, name, value, now))
        
        conn.commit()
        conn.close()
        print(f"💾 Saved {len(cookies)} cookies to session")
    
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
            
            try:
                await page.goto("https://www.meta.ai")
                
                # Submit prompt
                await page.evaluate("""(prompt) => {
                    const textarea = document.querySelector('textarea[data-testid="composer-input"]');
                    if (textarea) {
                        textarea.value = prompt;
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", prompt)
                await page.keyboard.press("Enter")
                
                # Wait for generation
                await asyncio.sleep(15)
                
                # Extract image URLs
                images = await page.query_selector_all('img[data-testid="generated-image"]')
                image_urls = []
                
                for img in images[:num_images]:
                    src = await img.get_attribute('src')
                    if src and src not in image_urls:
                        image_urls.append(src)
                
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
                # Navigate to /media page
                await page.goto("https://www.meta.ai/media")
                await asyncio.sleep(3)
                
                # Enter prompt using JavaScript
                await page.evaluate("""(prompt) => {
                    const ta = document.querySelector('textarea[data-testid="composer-input"]');
                    if (ta) {
                        ta.value = prompt;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }""", prompt)
                await asyncio.sleep(1)
                
                # Submit
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                
                # Wait for videos (poll every 3 seconds for 30 seconds)
                video_urls = []
                for i in range(10):
                    await asyncio.sleep(3)
                    
                    # Check for videos
                    videos = await page.query_selector_all('video[src*="fbcdn.net"], video[src*="video-sin"]')
                    
                    if videos:
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls:
                                video_urls.append(src)
                        
                        if len(video_urls) >= 4:
                            break
                
                await context.close()
                
                return {
                    "success": len(video_urls) > 0,
                    "prompt": prompt,
                    "video_urls": video_urls[:4],
                    "count": len(video_urls)
                }
                
            except Exception as e:
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
