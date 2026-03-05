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
        
        print(f"URL: {page.url}")
        
        # Try clicking on first generated image
        images = await page.query_selector_all('img[data-testid="generated-image"]')
        print(f"Found {len(images)} images")
        
        if images:
            print("Clicking first image...")
            await images[0].click()
            await asyncio.sleep(3)
            
            await page.screenshot(path="debug_after_image_click.png")
            print("Screenshot after image click saved")
            
            # Check for any modal or new elements
            modals = await page.query_selector_all('[role="dialog"], [data-testid*="modal"], [data-testid*="media"]')
            print(f"Modal/media elements: {len(modals)}")
            
            # Look for Animate in new context
            buttons = await page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if text and 'Animate' in text:
                    print(f"Found Animate: {text[:50]}")
                    # Click it
                    await btn.evaluate("b => b.click()")
                    print("Clicked via JS")
                    break
        
        await asyncio.sleep(15)
        
        # Check for video
        videos = await page.query_selector_all('video')
        print(f"Videos: {len(videos)}")
        
        # Check for any new URLs or download links
        links = await page.query_selector_all('a[href*="blob"], a[href*=".mp4"], a[download]')
        print(f"Video/download links: {len(links)}")
        
        await page.screenshot(path="debug_final2.png")
        await context.close()

asyncio.run(debug())
