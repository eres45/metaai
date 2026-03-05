"""
Try animating from an existing prompt page like the working videos.
"""
import asyncio
from playwright.async_api import async_playwright
import requests
from pathlib import Path
from datetime import datetime


async def animate_existing():
    """Try to animate from an existing image prompt."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        # Step 1: Generate a new image first
        print("Step 1: Generate new image...")
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        
        prompt = "A cat playing piano"
        await page.evaluate("""(p) => {
            const ta = document.querySelector('textarea[data-testid="composer-input"]');
            if (ta) { ta.value = p; ta.dispatchEvent(new Event('input', { bubbles: true })); }
        }""", prompt)
        await page.keyboard.press("Enter")
        await asyncio.sleep(15)
        
        # Get the current URL (should be a prompt page)
        current_url = page.url
        print(f"  URL after generation: {current_url}")
        
        # Step 2: Look for the image and Animate button on this page
        print("\nStep 2: Looking for Animate on main page...")
        await page.screenshot(path="debug_main_with_images.png")
        
        # Check for assistant message containers
        assistant_msgs = await page.query_selector_all('[data-testid="assistant-message"]')
        print(f"  Found {len(assistant_msgs)} assistant messages")
        
        for i, msg in enumerate(assistant_msgs[-2:]):  # Check last 2
            print(f"\n  Checking message {i}...")
            
            # Look for Animate button within this message
            buttons = await msg.query_selector_all('button')
            print(f"    Buttons found: {len(buttons)}")
            
            for btn in buttons:
                text = await btn.text_content()
                if text:
                    print(f"      - '{text.strip()}'")
                    if 'animate' in text.lower():
                        print(f"      >>> Clicking Animate via JavaScript!")
                        # Use JavaScript click since button may be hidden
                        await btn.evaluate("btn => { btn.scrollIntoView(); btn.click(); btn.dispatchEvent(new MouseEvent('click', { bubbles: true })); }")
                        await asyncio.sleep(2)
                        
                        # Check for Custom animate
                        custom = await page.query_selector('button:has-text("Custom animate")')
                        if custom:
                            print(f"      >>> Clicking Custom animate!")
                            await custom.click()
                            await asyncio.sleep(2)
                        
                        # Now wait for video
                        print("\n  Waiting for video...")
                        for attempt in range(20):  # 100 seconds
                            await asyncio.sleep(5)
                            
                            # Check for videos with fbcdn URLs
                            videos = await page.query_selector_all('video[src*="fbcdn"], video[src*="video-sin"]')
                            if videos:
                                print(f"      🎉 Found {len(videos)} videos after {(attempt+1)*5}s!")
                                for vid in videos:
                                    src = await vid.get_attribute('src')
                                    if src:
                                        print(f"        URL: {src[:70]}...")
                                break
                            
                            if (attempt + 1) % 4 == 0:
                                print(f"      Still waiting... ({(attempt+1)*5}s)")
                        
                        await page.screenshot(path=f"debug_after_animate_msg_{i}.png")
                        break
        
        # Step 3: If no video yet, try clicking View media
        if True:  # Always try this
            print("\nStep 3: Trying View media approach...")
            view_links = await page.query_selector_all('a[aria-label="View media"]')
            print(f"  Found {len(view_links)} View media links")
            
            if view_links:
                # Click the last one (most recent)
                await view_links[-1].click()
                print("  Clicked View media (last one)")
                await asyncio.sleep(3)
                
                print(f"  URL: {page.url}")
                await page.screenshot(path="debug_view_media_page.png")
                
                # Look for Animate on this page
                print("  Looking for Animate button...")
                animate_btn = await page.query_selector('button:has-text("Animate")')
                
                if animate_btn:
                    print("  ✅ Found Animate, clicking...")
                    await animate_btn.click(force=True)
                    await asyncio.sleep(2)
                    
                    # Handle Custom animate
                    custom = await page.query_selector('button:has-text("Custom animate")')
                    if custom:
                        await custom.click()
                        await asyncio.sleep(2)
                    
                    print("  Waiting for video on media page...")
                    for attempt in range(20):
                        await asyncio.sleep(5)
                        
                        # Check for videos
                        videos = await page.query_selector_all('video[src*="fbcdn"], video[src*="video-sin"]')
                        all_vids = await page.query_selector_all('video')
                        
                        print(f"    Attempt {attempt+1}: {len(videos)} fbcdn videos, {len(all_vids)} total videos")
                        
                        if videos:
                            print(f"    🎉 SUCCESS! Videos found!")
                            for i, vid in enumerate(videos[:2]):
                                src = await vid.get_attribute('src')
                                print(f"      Video {i+1}: {src[:70]}...")
                            break
                        
                        if (attempt + 1) % 4 == 0:
                            await page.screenshot(path=f"debug_media_wait_{(attempt+1)*5}s.png")
                else:
                    print("  ❌ No Animate button found on media page")
        
        await page.screenshot(path="debug_final.png")
        await context.close()
        print("\n✅ Done - check screenshots")


if __name__ == "__main__":
    print("="*80)
    print("Animate Existing Image")
    print("="*80)
    asyncio.run(animate_existing())
