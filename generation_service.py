"""
Unified Meta AI Generation Service
Supports both image and video generation with downloads.
"""
import sys
import json
import os
import requests
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Add metaai-api to path
sys.path.insert(0, 'metaai-api/src')

from metaai_api import MetaAI


class MetaGenerationService:
    """Service for generating and downloading images/videos from Meta AI."""
    
    def __init__(self, cookies_path: str = "meta_cookies.json"):
        """Initialize with cookies from file."""
        self.cookies = self._load_cookies(cookies_path)
        self.ai = None
        
        if self.cookies:
            try:
                self.ai = MetaAI(cookies=self.cookies)
                print("✅ MetaAI initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize MetaAI: {e}")
        else:
            print("⚠️ No cookies available. Run extract_cookies.py first.")
    
    def _load_cookies(self, path: str) -> Optional[Dict]:
        """Load cookies from JSON file."""
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return json.load(f)
    
    def generate_images(
        self, 
        prompt: str, 
        num_images: int = 4, 
        orientation: str = "SQUARE"
    ) -> Dict:
        """
        Generate images from text prompt.
        
        Args:
            prompt: Text description of desired image
            num_images: Number of images to generate (1-4)
            orientation: "SQUARE", "LANDSCAPE", or "PORTRAIT"
        
        Returns:
            Dict with success status and image URLs
        """
        if not self.ai:
            return {"success": False, "error": "MetaAI not initialized"}
        
        try:
            result = self.ai.generate_image_new(
                prompt=prompt,
                orientation=orientation,
                num_images=num_images
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_videos(
        self, 
        prompt: str, 
        num_videos: int = 1
    ) -> Dict:
        """
        Generate videos from text prompt.
        
        Args:
            prompt: Text description of desired video
            num_videos: Number of videos to generate
        
        Returns:
            Dict with success status and video URLs
        """
        if not self.ai:
            return {"success": False, "error": "MetaAI not initialized"}
        
        try:
            result = self.ai.generate_video_new(prompt=prompt)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def download_file(
        self, 
        url: str, 
        output_dir: str = "downloads",
        filename: Optional[str] = None
    ) -> str:
        """
        Download a file from URL.
        
        Args:
            url: Direct file URL
            output_dir: Directory to save file
            filename: Optional custom filename
        
        Returns:
            Path to downloaded file
        """
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = self._get_extension_from_url(url)
            filename = f"meta_{timestamp}{ext}"
        
        filepath = os.path.join(output_dir, filename)
        
        # Download file
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def _get_extension_from_url(self, url: str) -> str:
        """Extract file extension from URL."""
        if '.mp4' in url:
            return '.mp4'
        elif '.jpg' in url or '.jpeg' in url:
            return '.jpg'
        elif '.png' in url:
            return '.png'
        elif '.webp' in url:
            return '.webp'
        else:
            return '.bin'
    
    def generate_and_download_images(
        self,
        prompt: str,
        num_images: int = 4,
        orientation: str = "SQUARE",
        output_dir: str = "downloads/images"
    ) -> Dict:
        """
        Generate images and download them.
        
        Returns:
            Dict with generation result and local file paths
        """
        result = self.generate_images(prompt, num_images, orientation)
        
        if result.get("success") and result.get("image_urls"):
            downloaded_files = []
            for i, url in enumerate(result["image_urls"]):
                filename = f"image_{i+1}.jpg"
                filepath = self.download_file(url, output_dir, filename)
                if filepath:
                    downloaded_files.append(filepath)
            
            result["downloaded_files"] = downloaded_files
            print(f"✅ Downloaded {len(downloaded_files)} images to {output_dir}")
        
        return result
    
    def generate_and_download_videos(
        self,
        prompt: str,
        num_videos: int = 1,
        output_dir: str = "downloads/videos"
    ) -> Dict:
        """
        Generate videos and download them.
        
        Returns:
            Dict with generation result and local file paths
        """
        result = self.generate_videos(prompt, num_videos)
        
        if result.get("success") and result.get("video_urls"):
            downloaded_files = []
            for i, url in enumerate(result["video_urls"]):
                filename = f"video_{i+1}.mp4"
                filepath = self.download_file(url, output_dir, filename)
                if filepath:
                    downloaded_files.append(filepath)
            
            result["downloaded_files"] = downloaded_files
            print(f"✅ Downloaded {len(downloaded_files)} videos to {output_dir}")
        
        return result


# Test the service
if __name__ == "__main__":
    print("="*80)
    print("Meta AI Generation Service Test")
    print("="*80)
    
    service = MetaGenerationService()
    
    if service.ai:
        # Test image generation
        print("\n[1] Testing Image Generation")
        print("-"*80)
        img_result = service.generate_and_download_images(
            prompt="A serene mountain landscape at sunset",
            num_images=2,
            orientation="LANDSCAPE"
        )
        print(f"Image result: {json.dumps(img_result, indent=2)[:500]}...")
        
        # Test video generation
        print("\n[2] Testing Video Generation")
        print("-"*80)
        vid_result = service.generate_and_download_videos(
            prompt="A peaceful waterfall in a tropical forest"
        )
        print(f"Video result: {json.dumps(vid_result, indent=2)[:500]}...")
    else:
        print("\n⚠️ Service not initialized. Check cookies.")
