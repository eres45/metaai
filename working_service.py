"""
Working Meta AI Generation Service
Uses browser automation for images (confirmed working)
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
    """Working generation service using browser automation."""
    
    def __init__(self, user_data_dir: str = "./meta_session"):
        self.user_data_dir = user_data_dir
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
    
    async def generate_images(
        self, 
        prompt: str, 
        num_images: int = 4
    ) -> Dict:
        """
        Generate images using browser automation.
        Returns dict with image URLs.
        """
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await context.new_page()
            
            try:
                # Navigate to Meta AI
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
                return {
                    "success": False,
                    "error": str(e),
                    "prompt": prompt
                }
    
    def download_file(
        self, 
        url: str, 
        output_dir: str = "downloads",
        filename: Optional[str] = None
    ) -> Optional[str]:
        """Download file from URL."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = self._get_extension(url)
            filename = f"meta_{timestamp}_{hash(url) % 10000}{ext}"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filepath
        except Exception as e:
            print(f"Download failed: {e}")
            return None
    
    def _get_extension(self, url: str) -> str:
        """Get file extension from URL."""
        if '.mp4' in url:
            return '.mp4'
        elif '.jpg' in url or '.jpeg' in url:
            return '.jpg'
        elif '.png' in url:
            return '.png'
        elif '.webp' in url:
            return '.webp'
        else:
            return '.jpg'
    
    async def generate_and_download_images(
        self,
        prompt: str,
        num_images: int = 4,
        output_subdir: str = "images"
    ) -> Dict:
        """Generate images and download them."""
        result = await self.generate_images(prompt, num_images)
        
        output_dir = self.downloads_dir / output_subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = []
        if result.get("success") and result.get("image_urls"):
            for i, url in enumerate(result["image_urls"]):
                ext = self._get_extension(url)
                filename = f"image_{i+1}{ext}"
                filepath = self.download_file(url, str(output_dir), filename)
                if filepath:
                    downloaded.append(filepath)
        
        result["downloaded_files"] = downloaded
        result["download_dir"] = str(output_dir)
        return result


# Singleton instance
_service = None

def get_service():
    global _service
    if _service is None:
        _service = MetaGenerationService()
    return _service
