"""
Navigate to Meta AI Create section via main page.
"""
import asyncio
from playwright.async_api import async_playwright


async def explore_create():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Start at main page
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        print(f"Main page: {page.url}")
        
        # Click on "Create" in sidebar
        create_link = await page.query_selector('a[href="/media"]')
        if create_link:
            print("Clicking Create link...")
            await create_link.click()
            await asyncio.sleep(3)
            print(f"After Create click: {page.url}")
        
        # Get all buttons
        buttons = await page.query_selector_all('button')
        print(f"\nFound {len(buttons)} buttons:")
        for btn in buttons[:30]:
            text = await btn.text_content()
            if text and len(text.strip()) > 0:
                print(f"  - {text.strip()[:50]}")
        
        # Look for textareas
        textareas = await page.query_selector_all('textarea')
        print(f"\nFound {len(textareas)} textareas:")
        for ta in textareas:
            placeholder = await ta.get_attribute('placeholder')
            testid = await ta.get_attribute('data-testid')
            print(f"  - testid: {testid}, placeholder: {placeholder}")
        
        await page.screenshot(path="debug_after_create_click.png")
        
        await context.close()

asyncio.run(explore_create())
