"""
Click the bottom "Create" button to access video creation.
"""
import asyncio
from playwright.async_api import async_playwright


async def click_bottom_create():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to Create page
        await page.goto("https://www.meta.ai/media")
        await asyncio.sleep(5)
        print(f"URL: {page.url}")
        await page.screenshot(path="debug_before_click.png")
        
        # Look for the bottom "Create" button (not the sidebar one)
        print("\nLooking for bottom Create button...")
        
        # Get all buttons and find the last "Create" button
        buttons = await page.query_selector_all('button')
        create_buttons = []
        
        for i, btn in enumerate(buttons):
            text = await btn.text_content()
            if text and text.strip() == 'Create':
                create_buttons.append((i, btn))
                print(f"  Found Create button at index {i}")
        
        if create_buttons:
            # Click the last one (likely the bottom one)
            last_create = create_buttons[-1][1]
            print(f"\nClicking last Create button (index {create_buttons[-1][0]})...")
            await last_create.click()
            await asyncio.sleep(3)
            
            print(f"URL after click: {page.url}")
            await page.screenshot(path="debug_after_bottom_create.png")
            
            # Check what appeared
            page_text = await page.evaluate("""() => document.body.innerText""")
            print("\n=== PAGE TEXT AFTER CLICK ===")
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]
            for line in lines[:30]:
                print(f"  {line}")
            
            # Look for video/image options
            print("\n=== LOOKING FOR VIDEO/IMAGE OPTIONS ===")
            buttons_after = await page.query_selector_all('button')
            for btn in buttons_after[:20]:
                text = await btn.text_content()
                if text and len(text.strip()) > 0:
                    print(f"  Button: '{text.strip()}'")
        else:
            print("No Create button found")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Clicking Bottom Create Button")
    print("="*80)
    asyncio.run(click_bottom_create())
