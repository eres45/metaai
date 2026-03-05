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
        
        # Click the overlay link that says "View media"
        view_links = await page.query_selector_all('a[aria-label="View media"]')
        print(f"Found {len(view_links)} View media links")
        
        if view_links:
            href = await view_links[0].get_attribute('href')
            print(f"Navigating to: {href}")
            await view_links[0].click()
            await asyncio.sleep(5)
            
            print(f"After click URL: {page.url}")
            await page.screenshot(path="debug_media_view.png")
            
            # Look for Animate button on this page
            buttons = await page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if text and 'Animate' in text:
                    print(f"Found Animate: {text[:50]}")
                    await btn.evaluate("b => { b.click(); b.dispatchEvent(new MouseEvent('click', {bubbles: true})); }")
                    print("Clicked Animate")
                    break
            
            await asyncio.sleep(20)
            
            # Check for video
            videos = await page.query_selector_all('video')
            print(f"Videos: {len(videos)}")
            
            await page.screenshot(path="debug_after_animate2.png")
        
        await context.close()

asyncio.run(debug())
