"""
Debug video generation step by step with detailed logging.
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_video_generation():
    """Debug the video generation flow step by step."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        try:
            # Step 1: Generate images
            print("Step 1: Generating images...")
            await page.goto("https://www.meta.ai")
            await asyncio.sleep(3)
            print(f"  URL: {page.url}")
            await page.screenshot(path="debug_step1_start.png")
            
            # Submit prompt
            prompt = "A cat dancing"
            await page.evaluate("""(prompt) => {
                const ta = document.querySelector('textarea[data-testid="composer-input"]');
                if (ta) {
                    ta.value = prompt;
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""", prompt)
            await page.keyboard.press("Enter")
            print(f"  Submitted: {prompt}")
            
            # Wait for images
            await asyncio.sleep(15)
            await page.screenshot(path="debug_step2_images.png")
            print("  Images generated")
            
            # Check for images
            images = await page.query_selector_all('img[data-testid="generated-image"]')
            print(f"  Found {len(images)} images")
            
            # Check for View media links
            view_links = await page.query_selector_all('a[aria-label="View media"]')
            print(f"  Found {len(view_links)} View media links")
            
            if not view_links:
                print("  No View media links found - checking all links...")
                all_links = await page.query_selector_all('a')
                for link in all_links[:10]:
                    text = await link.text_content()
                    aria = await link.get_attribute('aria-label')
                    href = await link.get_attribute('href')
                    if text or aria:
                        print(f"    Link: text='{text}', aria='{aria}', href='{href}'")
            
            # Step 2: Click on first image to view
            print("\nStep 2: Clicking View media...")
            if view_links:
                await view_links[0].click()
                print("  Clicked View media")
                await asyncio.sleep(3)
                print(f"  URL after click: {page.url}")
                await page.screenshot(path="debug_step3_after_view.png")
            else:
                print("  ERROR: No View media link to click!")
            
            # Step 3: Look for Animate button
            print("\nStep 3: Looking for Animate button...")
            
            # Take screenshot of current state
            await page.screenshot(path="debug_step4_looking_animate.png")
            
            # Look for Animate button in different ways
            print("  Checking for Animate buttons...")
            all_buttons = await page.query_selector_all('button')
            print(f"  Total buttons: {len(all_buttons)}")
            
            animate_found = False
            for i, btn in enumerate(all_buttons[:30]):
                text = await btn.text_content()
                if text and 'animate' in text.lower():
                    print(f"    Button {i}: '{text.strip()}'")
                    animate_found = True
            
            if not animate_found:
                print("  No Animate button found in text search")
                
                # Check page text
                page_text = await page.evaluate("""() => document.body.innerText""")
                if 'animate' in page_text.lower():
                    lines = [l.strip() for l in page_text.split('\n') if 'animate' in l.lower()]
                    print(f"  'Animate' text found on page:")
                    for line in lines[:5]:
                        print(f"    - {line}")
            
            # Try to click Animate with JavaScript
            print("\nStep 4: Clicking Animate via JavaScript...")
            click_result = await page.evaluate("""() => {
                // Find assistant message container
                const assistantMsg = document.querySelector('[data-testid="assistant-message"]');
                if (!assistantMsg) {
                    return 'no-assistant-message';
                }
                
                // Find Animate button within it
                const buttons = Array.from(assistantMsg.querySelectorAll('button'));
                const animateBtn = buttons.find(b => 
                    b.textContent && b.textContent.trim().includes('Animate')
                );
                
                if (animateBtn) {
                    animateBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    animateBtn.click();
                    animateBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    return 'clicked-animate';
                }
                
                return 'no-animate-found';
            }""")
            print(f"  Result: {click_result}")
            
            if click_result == 'clicked-animate':
                print("  Animate button clicked, waiting for video...")
                await asyncio.sleep(5)
                await page.screenshot(path="debug_step5_after_animate.png")
                
                # Wait for video with short polling
                for attempt in range(12):  # 60 seconds total
                    await asyncio.sleep(5)
                    
                    # Check for video elements
                    videos = await page.query_selector_all('video')
                    if videos:
                        print(f"  🎉 Found {len(videos)} videos after {(attempt+1)*5}s!")
                        for i, vid in enumerate(videos):
                            src = await vid.get_attribute('src')
                            print(f"    Video {i+1}: {src[:70]}..." if src else f"    Video {i+1}: no src")
                        break
                    else:
                        if (attempt + 1) % 2 == 0:
                            print(f"  Still waiting... ({(attempt+1)*5}s)")
                else:
                    print("  No videos found after 60s")
                    await page.screenshot(path="debug_step6_no_video.png")
                    
                    # Check what's on the page
                    page_text = await page.evaluate("""() => document.body.innerText""")
                    if 'video' in page_text.lower() or 'generating' in page_text.lower():
                        print("  Video-related text found on page")
            else:
                print(f"  Could not click Animate: {click_result}")
                
                # List all assistant message containers
                assistant_msgs = await page.query_selector_all('[data-testid="assistant-message"]')
                print(f"  Found {len(assistant_msgs)} assistant messages")
                
                for i, msg in enumerate(assistant_msgs):
                    buttons = await msg.query_selector_all('button')
                    print(f"    Message {i}: {len(buttons)} buttons")
                    for btn in buttons:
                        text = await btn.text_content()
                        if text:
                            print(f"      - {text.strip()}")
            
            await context.close()
            print("\n✅ Debug complete - check screenshots")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Video Generation Debug")
    print("="*80)
    asyncio.run(debug_video_generation())
