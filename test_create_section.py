"""
Test Meta AI Create section for video generation.
"""
import asyncio
from playwright.async_api import async_playwright


async def test_create_section():
    """Test navigating to Create section and generating video."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=False,  # Set to True after testing
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        # Go to main Meta AI page
        await page.goto("https://www.meta.ai")
        print(f"Main page URL: {page.url}")
        
        await asyncio.sleep(3)
        
        # Look for Create button/link
        buttons = await page.query_selector_all('button, a')
        print("\nLooking for Create button:")
        for btn in buttons:
            text = await btn.text_content()
            if text and 'create' in text.lower():
                print(f"  Found: {text[:50]}")
                href = await btn.get_attribute('href')
                if href:
                    print(f"    href: {href}")
        
        # Try navigating to /create directly
        await page.goto("https://www.meta.ai/create")
        print(f"\nCreate page URL: {page.url}")
        await asyncio.sleep(3)
        
        # Look for Create video button and click it
        print("\nClicking 'Create video'...")
        create_video_btn = await page.query_selector('button:has-text("Create video")')
        if create_video_btn:
            await create_video_btn.click()
            await asyncio.sleep(3)
            print(f"After click URL: {page.url}")
            await page.screenshot(path="debug_create_video.png")
        
        # Look for prompt input
        print("\nLooking for prompt input:")
        textareas = await page.query_selector_all('textarea, input[type="text"]')
        for ta in textareas:
            placeholder = await ta.get_attribute('placeholder')
            testid = await ta.get_attribute('data-testid')
            print(f"  Textarea/input - testid: {testid}, placeholder: {placeholder}")
        
        # Look for generate buttons
        print("\nLooking for generate buttons:")
        gen_buttons = await page.query_selector_all('button')
        for btn in gen_buttons:
            text = await btn.text_content()
            if text:
                print(f"  Button: {text[:50]}")
        
        await asyncio.sleep(5)
        await context.close()


if __name__ == "__main__":
    asyncio.run(test_create_section())
