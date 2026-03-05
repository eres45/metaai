"""
Find the video creation interface on Meta AI.
"""
import asyncio
from playwright.async_api import async_playwright


async def find_video_interface():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=False,  # Visible to see what's happening
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        # Try different URLs for video creation
        urls_to_try = [
            "https://www.meta.ai/create",
            "https://www.meta.ai/video",
            "https://www.meta.ai/media",
            "https://www.meta.ai/",
        ]
        
        for url in urls_to_try:
            print(f"\n{'='*60}")
            print(f"Trying: {url}")
            print('='*60)
            
            await page.goto(url)
            await asyncio.sleep(5)
            
            print(f"Current URL: {page.url}")
            
            # Get page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Check for specific text
            page_text = await page.evaluate("""() => document.body.innerText""")
            
            # Look for video-related content
            if 'video' in page_text.lower():
                print("✅ Page contains 'video' text")
                lines = [l.strip() for l in page_text.split('\n') if l.strip() and 'video' in l.lower()]
                for line in lines[:10]:
                    print(f"  - {line}")
            
            # Look for prompt inputs
            inputs = await page.query_selector_all('textarea, input[type="text"]')
            print(f"\nFound {len(inputs)} text inputs:")
            for inp in inputs:
                placeholder = await inp.get_attribute('placeholder')
                testid = await inp.get_attribute('data-testid')
                print(f"  - placeholder: {placeholder}, testid: {testid}")
            
            # Look for create/generate buttons
            buttons = await page.query_selector_all('button')
            print(f"\nRelevant buttons:")
            for btn in buttons[:20]:
                text = await btn.text_content()
                if text and any(word in text.lower() for word in ['create', 'generate', 'video', 'image']):
                    print(f"  - {text.strip()}")
            
            await page.screenshot(path=f"debug_url_{url.replace('/', '_').replace(':', '')}.png")
        
        await context.close()

asyncio.run(find_video_interface())
