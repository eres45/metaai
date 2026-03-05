import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        await page.goto('https://www.meta.ai')
        
        await page.evaluate("""(prompt) => {
            const textarea = document.querySelector('textarea[data-testid="composer-input"]');
            if (textarea) {
                textarea.value = 'A cat dancing';
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }""")
        await page.keyboard.press('Enter')
        await asyncio.sleep(15)
        
        # Click View media
        view_links = await page.query_selector_all('a[aria-label="View media"]')
        if view_links:
            await view_links[0].click()
            await asyncio.sleep(5)
            
            print(f"On create page: {page.url}")
            
            # Click Animate
            await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.textContent && b.textContent.includes('Animate'));
                if (btn) {
                    btn.scrollIntoView({block: 'center'});
                    btn.click();
                    btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    return 'clicked';
                }
                return 'not-found';
            }""")
            
            print("Animate clicked, waiting for video...")
            
            # Wait longer and poll for video
            for i in range(12):  # 2 minutes total
                await asyncio.sleep(10)
                
                # Check for video
                videos = await page.query_selector_all('video')
                if videos:
                    print(f"Video found after {(i+1)*10}s!")
                    src = await videos[0].get_attribute('src')
                    print(f"Video src: {src}")
                    break
                
                # Check for any video-related elements
                vid_elements = await page.query_selector_all('[data-testid*="video"], .video-player, [class*="video"]')
                print(f"  {i+1}: Videos={len(videos)}, Vid elements={len(vid_elements)}")
                
                # Check if page changed
                current_url = page.url
                if 'video' in current_url or 'animate' in current_url:
                    print(f"  URL changed to: {current_url}")
            
            await page.screenshot(path="debug_long_wait.png")
            print("Final screenshot saved")
        
        await context.close()

asyncio.run(debug())
