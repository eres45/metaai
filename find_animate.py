"""
Find Animate button on the media/create page.
"""
import asyncio
from playwright.async_api import async_playwright


async def find_animate_on_media_page():
    """Find and click Animate button on media page."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        # Generate images first
        print("Generating images...")
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        
        await page.evaluate("""(p) => {
            const ta = document.querySelector('textarea[data-testid="composer-input"]');
            if (ta) { ta.value = p; ta.dispatchEvent(new Event('input', { bubbles: true })); }
        }""", "A cat dancing")
        await page.keyboard.press("Enter")
        await asyncio.sleep(15)
        
        # Click View media on first image
        print("Clicking View media...")
        view_link = await page.query_selector('a[aria-label="View media"]')
        if view_link:
            await view_link.click()
            await asyncio.sleep(3)
        
        print(f"Current URL: {page.url}")
        await page.screenshot(path="debug_media_before_animate.png")
        
        # Look for Animate button using various methods
        print("\nSearching for Animate button...")
        
        # Method 1: Look for button with text "Animate"
        animate_btn = await page.query_selector('button:has-text("Animate")')
        if animate_btn:
            print("✅ Found Animate button with :has-text selector")
            await animate_btn.click()
            print("✅ Clicked Animate button")
        else:
            print("❌ Method 1: :has-text selector failed")
        
        # Method 2: JavaScript approach on entire page
        if not animate_btn:
            print("\nMethod 2: JavaScript search...")
            result = await page.evaluate("""() => {
                const allButtons = Array.from(document.querySelectorAll('button'));
                const animateBtn = allButtons.find(b => 
                    b.textContent && b.textContent.trim() === 'Animate'
                );
                
                if (animateBtn) {
                    animateBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    // Click multiple ways
                    animateBtn.click();
                    animateBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    return { found: true, text: animateBtn.textContent.trim() };
                }
                
                // List all buttons for debugging
                const buttonTexts = allButtons
                    .map(b => b.textContent?.trim())
                    .filter(t => t && t.length > 0)
                    .slice(0, 20);
                
                return { found: false, buttons: buttonTexts };
            }""")
            
            print(f"  Result: {result}")
            
            if result.get('found'):
                print("✅ Clicked Animate via JavaScript")
                await asyncio.sleep(3)
            else:
                print(f"  Available buttons: {result.get('buttons', [])}")
        
        # Check if Custom animate is there instead
        print("\nChecking for Custom animate...")
        custom_animate = await page.query_selector('button:has-text("Custom animate")')
        if custom_animate:
            print("✅ Found Custom animate button")
            await custom_animate.click()
            print("✅ Clicked Custom animate")
            await asyncio.sleep(3)
        
        # Take screenshot after clicking
        await page.screenshot(path="debug_media_after_animate.png")
        print(f"\nURL after animate: {page.url}")
        
        # Wait and check for videos
        print("\nWaiting for video (30s)...")
        await asyncio.sleep(30)
        
        videos = await page.query_selector_all('video')
        print(f"Found {len(videos)} video elements")
        
        for i, vid in enumerate(videos):
            src = await vid.get_attribute('src')
            if src:
                print(f"  Video {i+1}: {src[:70]}...")
        
        await page.screenshot(path="debug_media_final.png")
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Finding Animate Button")
    print("="*80)
    asyncio.run(find_animate_on_media_page())
