"""
Test video generation with longer wait and better detection.
"""
import asyncio
from playwright.async_api import async_playwright
import requests
from pathlib import Path
from datetime import datetime


async def test_video_with_polling():
    """Test video generation with aggressive polling."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        print("Step 1: Generate images...")
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        
        await page.evaluate("""(p) => {
            const ta = document.querySelector('textarea[data-testid="composer-input"]');
            if (ta) { ta.value = p; ta.dispatchEvent(new Event('input', { bubbles: true })); }
        }""", "A cat playing piano")
        await page.keyboard.press("Enter")
        await asyncio.sleep(15)
        
        print("Step 2: Click View media on first image...")
        view_link = await page.query_selector('a[aria-label="View media"]')
        if view_link:
            await view_link.click()
            await asyncio.sleep(3)
        
        print(f"  URL: {page.url}")
        
        print("Step 3: Click Animate button...")
        # Use force click to bypass any overlays
        await page.click('button:has-text("Animate")', force=True)
        print("  ✅ Clicked Animate with force=True")
        await asyncio.sleep(2)
        
        # Check if Custom animate appeared
        custom = await page.query_selector('button:has-text("Custom animate")')
        if custom:
            print("  Found Custom animate, clicking...")
            await custom.click()
            await asyncio.sleep(2)
        
        await page.screenshot(path="debug_after_animate_click.png")
        
        print("Step 4: Polling for video (up to 90 seconds)...")
        video_url = None
        
        for i in range(18):  # 90 seconds total
            await asyncio.sleep(5)
            
            # Check for video elements
            videos = await page.query_selector_all('video')
            for vid in videos:
                src = await vid.get_attribute('src')
                if src and 'blob' not in src and 'http' in src:
                    video_url = src
                    print(f"  🎉 Video found after {(i+1)*5}s: {src[:60]}...")
                    break
            
            if video_url:
                break
            
            # Also check for download links
            links = await page.query_selector_all('a[href]')
            for link in links:
                href = await link.get_attribute('href')
                if href and ('.mp4' in href or 'video' in href.lower()):
                    if href not in [video_url]:
                        video_url = href
                        print(f"  🎉 Video link found: {href[:60]}...")
                        break
            
            if video_url:
                break
            
            if (i + 1) % 6 == 0:  # Every 30 seconds
                print(f"  Still polling... ({(i+1)*5}s elapsed)")
                await page.screenshot(path=f"debug_polling_{(i+1)*5}s.png")
        
        # Final screenshot
        await page.screenshot(path="debug_final_video_check.png")
        
        if video_url:
            print(f"\n✅ SUCCESS! Video URL: {video_url[:70]}...")
            
            # Download it
            print("Downloading video...")
            try:
                response = requests.get(video_url, stream=True, timeout=120)
                if response.status_code == 200:
                    filepath = f"downloads/videos/video_{datetime.now().strftime('%H%M%S')}.mp4"
                    Path("downloads/videos").mkdir(parents=True, exist_ok=True)
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Downloaded to: {filepath}")
                else:
                    print(f"❌ Download failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ Download error: {e}")
        else:
            print("\n❌ No video found after 90 seconds")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Video Generation Test with Polling")
    print("="*80)
    asyncio.run(test_video_with_polling())
