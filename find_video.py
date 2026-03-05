"""
Find the video creation interface inside Meta AI Create section.
"""
import asyncio
from playwright.async_api import async_playwright


async def find_video_creation():
    """Find video creation interface."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to main page
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        print(f"Main page: {page.url}")
        
        # Click Create
        create_link = await page.query_selector('a:has-text("Create")')
        if create_link:
            await create_link.click()
            await asyncio.sleep(5)
            print(f"After Create click: {page.url}")
            await page.screenshot(path="debug_create_clicked.png")
        
        # Now look for video-specific options
        print("\n=== ALL CLICKABLE ELEMENTS ===")
        elements = await page.query_selector_all('button, a[href]')
        for i, el in enumerate(elements[:50]):
            text = await el.text_content()
            href = await el.get_attribute('href')
            if text and len(text.strip()) > 2:
                print(f"{i+1}. {text.strip()[:40]} | href: {href}")
        
        # Look for "video" text specifically
        print("\n=== ELEMENTS WITH 'VIDEO' ===")
        page_text = await page.evaluate("""() => document.body.innerText""")
        if 'video' in page_text.lower():
            lines = [l.strip() for l in page_text.split('\n') 
                     if l.strip() and 'video' in l.lower()]
            for line in lines[:15]:
                print(f"  - {line}")
        
        await context.close()


if __name__ == "__main__":
    asyncio.run(find_video_creation())
