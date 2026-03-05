import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to media page
        await page.goto('https://www.meta.ai/media')
        await asyncio.sleep(5)
        
        print(f"URL: {page.url}")
        
        # Get page text
        page_text = await page.evaluate("""() => document.body.innerText""")
        print("\n=== PAGE TEXT (first 50 lines) ===")
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        for line in lines[:50]:
            print(f"  {line}")
        
        # Look for all clickable elements with text
        print("\n=== CLICKABLE ELEMENTS ===")
        elements = await page.query_selector_all('button, a[href], [role="button"]')
        for el in elements[:40]:
            text = await el.text_content()
            tag = await el.evaluate('e => e.tagName')
            href = await el.get_attribute('href')
            if text and len(text.strip()) > 0:
                print(f"  {tag}: '{text.strip()[:50]}' | href: {href}")
        
        # Check for sidebar/menu items
        print("\n=== SIDEBAR ELEMENTS ===")
        sidebar_items = await page.query_selector_all('[data-slot="sidebar"] button, [data-slot="sidebar"] a')
        for item in sidebar_items[:20]:
            text = await item.text_content()
            if text:
                href = await item.get_attribute('href')
                print(f"  {text.strip()[:40]} | href: {href}")
        
        await page.screenshot(path="debug_media_full.png")
        print("\nScreenshot saved to debug_media_full.png")
        
        await context.close()

asyncio.run(debug())
