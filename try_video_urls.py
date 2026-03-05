"""
Try different URLs to find video creation interface.
"""
import asyncio
from playwright.async_api import async_playwright


async def try_video_urls():
    urls_to_try = [
        "https://www.meta.ai/create",
        "https://www.meta.ai/create?type=video",
        "https://www.meta.ai/video",
        "https://www.meta.ai/media?type=video",
    ]
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        for url in urls_to_try:
            print(f"\n{'='*60}")
            print(f"Trying: {url}")
            print('='*60)
            
            await page.goto(url)
            await asyncio.sleep(5)
            
            print(f"Final URL: {page.url}")
            
            # Check for video-specific content
            page_text = await page.evaluate("""() => document.body.innerText""")
            
            # Look for video creation indicators
            if 'video' in page_text.lower() and ('create' in page_text.lower() or 'generate' in page_text.lower()):
                print("✅ Video creation indicators found!")
                lines = [l.strip() for l in page_text.split('\n') 
                        if 'video' in l.lower() or 'create' in l.lower() or 'generate' in l.lower()]
                for line in lines[:10]:
                    print(f"  {line}")
                
                # Look for input
                inputs = await page.query_selector_all('textarea, input[type="text"]')
                print(f"\nInput fields: {len(inputs)}")
                for inp in inputs:
                    ph = await inp.get_attribute('placeholder')
                    print(f"  - {ph}")
                
                await page.screenshot(path=f"debug_url_{url.replace('/', '_').replace(':', '')}.png")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Trying Video URLs")
    print("="*80)
    asyncio.run(try_video_urls())
