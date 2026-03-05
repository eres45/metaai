"""
Click sidebar Create and look for video creation option.
"""
import asyncio
from playwright.async_api import async_playwright


async def click_sidebar_create():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=False,  # Make visible to see what's happening
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        # Step 1: Go to main page
        print("Step 1: Opening Meta AI...")
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        await page.screenshot(path="debug_step1_main.png")
        
        # Step 2: Click Create in sidebar
        print("\nStep 2: Clicking Create in sidebar...")
        create_link = await page.query_selector('a[href="/media"]')
        if create_link:
            text = await create_link.text_content()
            print(f"  Found: '{text}'")
            await create_link.click()
            await asyncio.sleep(5)  # Wait longer for interface to load
            print(f"  URL after click: {page.url}")
            await page.screenshot(path="debug_step2_after_create.png")
        
        # Step 3: Examine the entire page structure
        print("\nStep 3: Examining page structure...")
        
        # Get page text
        page_text = await page.evaluate("""() => document.body.innerText""")
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        
        print(f"  Total lines: {len(lines)}")
        print("\n  First 30 lines:")
        for i, line in enumerate(lines[:30]):
            print(f"    {i+1}. {line}")
        
        # Look for video/image related text
        print("\n  Looking for video/image/create related lines:")
        for line in lines:
            if any(word in line.lower() for word in ['video', 'image', 'create', 'generate', 'animate']):
                print(f"    -> {line}")
        
        # Step 4: Look at bottom of page
        print("\nStep 4: Looking at bottom area...")
        
        # Scroll to bottom
        await page.evaluate("""() => window.scrollTo(0, document.body.scrollHeight)""")
        await asyncio.sleep(2)
        await page.screenshot(path="debug_step4_bottom.png")
        
        # Get elements at bottom
        bottom_buttons = await page.query_selector_all('button')
        print(f"  Buttons at bottom:")
        for btn in bottom_buttons[-10:]:  # Last 10 buttons
            text = await btn.text_content()
            if text:
                print(f"    - '{text.strip()}'")
        
        # Step 5: Check for any hidden or modal elements
        print("\nStep 5: Checking for modals/overlays...")
        
        # Look for dialog/modal
        dialogs = await page.query_selector_all('[role="dialog"], [class*="modal"], [class*="overlay"]')
        print(f"  Dialogs/modals found: {len(dialogs)}")
        
        for i, dialog in enumerate(dialogs):
            text = await dialog.text_content()
            if text:
                print(f"    Dialog {i}: '{text[:100]}...'")
        
        # Check for hidden elements with video-related content
        all_elements = await page.query_selector_all('*')
        print(f"\n  Total elements: {len(all_elements)}")
        
        # Look for elements containing "video" text
        video_elements = []
        for el in all_elements[:100]:  # Check first 100
            try:
                text = await el.text_content()
                if text and 'video' in text.lower() and len(text.strip()) < 50:
                    tag = await el.evaluate("e => e.tagName")
                    video_elements.append((tag, text.strip()))
            except:
                pass
        
        print(f"  Elements with 'video' text: {len(video_elements)}")
        for tag, text in video_elements[:10]:
            print(f"    <{tag}>: '{text}'")
        
        print("\nWaiting 10 seconds for you to see...")
        await asyncio.sleep(10)
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Sidebar Create - Detailed Examination")
    print("="*80)
    asyncio.run(click_sidebar_create())
