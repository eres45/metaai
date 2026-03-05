"""
Simpler approach - check what's actually happening after Animate click.
"""
import asyncio
from playwright.async_api import async_playwright


async def simple_check():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        print("Step 1: Generate images...")
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        
        await page.evaluate("""(p) => {
            const ta = document.querySelector('textarea[data-testid="composer-input"]');
            if (ta) { ta.value = p; ta.dispatchEvent(new Event('input', { bubbles: true })); }
        }""", "A cat dancing")
        await page.keyboard.press("Enter")
        await asyncio.sleep(15)
        
        print("Step 2: Click View media...")
        await page.click('a[aria-label="View media"]')
        await asyncio.sleep(3)
        print(f"  URL: {page.url}")
        
        # Check page structure before animate
        print("\nBefore Animate - Page structure:")
        sections = await page.query_selector_all('section, div[class*="media"], div[class*="image"]')
        print(f"  Sections found: {len(sections)}")
        
        # Check for Animate button
        animate_btn = await page.query_selector('button:has-text("Animate")')
        if animate_btn:
            text = await animate_btn.text_content()
            print(f"  Animate button text: '{text}'")
        
        print("\nStep 3: Click Animate...")
        if animate_btn:
            await animate_btn.click()
            print("  Clicked Animate")
        await asyncio.sleep(2)
        
        # Check for Custom animate
        custom = await page.query_selector('button:has-text("Custom animate")')
        if custom:
            print("  Found Custom animate, clicking...")
            await custom.click()
            await asyncio.sleep(2)
        
        await page.screenshot(path="debug_after_both_clicks.png")
        
        print("\nStep 4: Check what changed...")
        
        # Wait 10 seconds and check
        await asyncio.sleep(10)
        
        # Look for any new elements
        print("  Checking for new elements:")
        
        # Video
        videos = await page.query_selector_all('video')
        print(f"    Videos: {len(videos)}")
        
        # Canvas (sometimes video is rendered on canvas)
        canvases = await page.query_selector_all('canvas')
        print(f"    Canvases: {len(canvases)}")
        
        # iframe
        iframes = await page.query_selector_all('iframe')
        print(f"    Iframes: {len(iframes)}")
        
        # Check if URL changed
        current_url = page.url
        print(f"    Current URL: {current_url}")
        
        # Check page text for clues
        page_text = await page.evaluate("""() => document.body.innerText.slice(0, 2000)""")
        print(f"\n  Page text preview:\n{page_text[:500]}...")
        
        await page.screenshot(path="debug_after_10s.png")
        
        # Try waiting another 20s and check again
        print("\nWaiting 20 more seconds...")
        await asyncio.sleep(20)
        
        videos = await page.query_selector_all('video')
        print(f"  Videos after 30s: {len(videos)}")
        
        if videos:
            for i, vid in enumerate(videos):
                src = await vid.get_attribute('src')
                print(f"    Video {i+1} src: {src[:70] if src else 'None'}...")
        
        await page.screenshot(path="debug_after_30s.png")
        
        await context.close()
        print("\nDone - check screenshots")


if __name__ == "__main__":
    print("="*80)
    print("Simple Video Check")
    print("="*80)
    asyncio.run(simple_check())
