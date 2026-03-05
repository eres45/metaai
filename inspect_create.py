"""
Inspect Create page to find video creation option.
"""
import asyncio
from playwright.async_api import async_playwright


async def inspect_create_page():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to Create page
        print("Going to Create page...")
        await page.goto("https://www.meta.ai/media")
        await asyncio.sleep(5)
        
        print(f"URL: {page.url}")
        
        # Get full page content
        page_text = await page.evaluate("""() => document.body.innerText""")
        print("\n=== PAGE CONTENT ===")
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        for i, line in enumerate(lines[:50]):
            print(f"{i+1}. {line}")
        
        # Look for all interactive elements
        print("\n=== ALL BUTTONS ===")
        buttons = await page.query_selector_all('button')
        for i, btn in enumerate(buttons):
            text = await btn.text_content()
            if text and len(text.strip()) > 0:
                print(f"  {i}: '{text.strip()}'")
        
        print("\n=== ALL LINKS ===")
        links = await page.query_selector_all('a[href]')
        for i, link in enumerate(links[:30]):
            text = await link.text_content()
            href = await link.get_attribute('href')
            if text:
                print(f"  {i}: '{text.strip()}' -> {href}")
        
        # Look for tabs or switches
        print("\n=== LOOKING FOR TABS/SWITCHES ===")
        tabs = await page.query_selector_all('[role="tab"], [role="switch"], .tab, [class*="tab"]')
        print(f"Found {len(tabs)} tabs/switches")
        for tab in tabs:
            text = await tab.text_content()
            if text:
                print(f"  Tab: '{text.strip()}'")
        
        # Check for video/image toggle
        print("\n=== CHECKING FOR VIDEO/IMAGE OPTIONS ===")
        options = await page.query_selector_all('[class*="video" i], [class*="image" i], [data-testid*="video" i], [data-testid*="image" i]')
        print(f"Found {len(options)} video/image related elements")
        
        await page.screenshot(path="debug_create_page_inspect.png")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Inspecting Create Page")
    print("="*80)
    asyncio.run(inspect_create_page())
