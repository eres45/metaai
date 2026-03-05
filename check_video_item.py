"""
Check existing video item to understand the video generation flow.
"""
import asyncio
from playwright.async_api import async_playwright


async def check_video_item():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to a video item from history
        print("Opening video item from history...")
        await page.goto("https://www.meta.ai/prompt/f3f87522-03d3-4ddf-abb4-c1470deded68")
        await asyncio.sleep(5)
        
        print(f"URL: {page.url}")
        
        # Get page text
        page_text = await page.evaluate("""() => document.body.innerText""")
        print("\n=== PAGE TEXT ===")
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        for i, line in enumerate(lines[:40]):
            print(f"{i+1}. {line}")
        
        # Look for video
        videos = await page.query_selector_all('video')
        print(f"\n=== FOUND {len(videos)} VIDEO ELEMENTS ===")
        
        for i, vid in enumerate(videos):
            src = await vid.get_attribute('src')
            print(f"Video {i+1}: {src[:80] if src else 'No src'}...")
            
            # Get parent element info
            parent = await vid.evaluate("el => el.parentElement?.className")
            print(f"  Parent class: {parent}")
        
        # Look for download links
        links = await page.query_selector_all('a[download], a[href*=".mp4"]')
        print(f"\n=== FOUND {len(links)} DOWNLOAD LINKS ===")
        for link in links:
            href = await link.get_attribute('href')
            text = await link.text_content()
            print(f"Link: {text[:30] if text else 'No text'} -> {href[:60] if href else 'No href'}...")
        
        # Check all media sources
        media = await page.query_selector_all('img[src], video[src], source[src]')
        print(f"\n=== ALL MEDIA ({len(media)} items) ===")
        for i, m in enumerate(media[:15]):
            tag = await m.evaluate("el => el.tagName")
            src = await m.get_attribute('src')
            if src:
                print(f"{i+1}. {tag}: {src[:70]}...")
        
        await page.screenshot(path="debug_video_item.png")
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Checking Video Item")
    print("="*80)
    asyncio.run(check_video_item())
