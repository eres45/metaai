"""
Deep inspection of video generation - check all elements and network.
"""
import asyncio
from playwright.async_api import async_playwright


async def deep_inspect():
    """Deep inspection of what happens after clicking Animate."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        # Monitor console logs
        logs = []
        page.on("console", lambda msg: logs.append(f"Console: {msg.text}"))
        page.on("pageerror", lambda err: logs.append(f"Error: {err}"))
        
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
        
        # Get full page HTML before animate
        html_before = await page.content()
        with open("debug_html_before.txt", "w", encoding="utf-8") as f:
            f.write(html_before[:50000])  # First 50k chars
        
        print("Step 3: Click Animate...")
        await page.click('button:has-text("Animate")', force=True)
        await asyncio.sleep(2)
        
        # Click Custom animate if present
        custom = await page.query_selector('button:has-text("Custom animate")')
        if custom:
            print("  Clicking Custom animate...")
            await custom.click()
            await asyncio.sleep(2)
        
        print("Step 4: Wait and inspect thoroughly...")
        
        for i in range(12):  # 60 seconds
            await asyncio.sleep(5)
            
            # Check 1: Video elements
            videos = await page.query_selector_all('video')
            print(f"  [{i+1}] Video elements: {len(videos)}")
            
            # Check 2: All media elements
            imgs = await page.query_selector_all('img[src*="fbcdn"]')
            print(f"      Images: {len(imgs)}")
            
            # Check 3: Any blob URLs
            blobs = await page.query_selector_all('[src^="blob:"], [href^="blob:"]')
            print(f"      Blob sources: {len(blobs)}")
            
            # Check 4: Sources with fbcdn
            all_srcs = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('*'))
                    .map(e => e.src || e.href)
                    .filter(s => s && s.includes('fbcdn'))
                    .slice(0, 10);
            }""")
            print(f"      FBCDN sources: {len(all_srcs)}")
            for src in all_srcs[:3]:
                print(f"        - {src[:70]}...")
            
            # Check 5: Any new sections or containers
            sections = await page.query_selector_all('section, [data-testid]')
            print(f"      Sections/containers: {len(sections)}")
            
            # Check 6: Check for "Generating" or progress text
            page_text = await page.evaluate("""() => document.body.innerText""")
            if any(word in page_text.lower() for word in ['generating', 'creating', 'animate']):
                lines = [l for l in page_text.split('\n') 
                        if any(w in l.lower() for w in ['generating', 'creating', 'animate'])]
                print(f"      Status text: {lines[:2]}")
        
        # Get HTML after
        html_after = await page.content()
        with open("debug_html_after.txt", "w", encoding="utf-8") as f:
            f.write(html_after[:50000])
        
        print("\nConsole logs:")
        for log in logs[-20:]:  # Last 20 logs
            print(f"  {log}")
        
        await page.screenshot(path="debug_inspect_final.png")
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Deep Inspection")
    print("="*80)
    asyncio.run(deep_inspect())
