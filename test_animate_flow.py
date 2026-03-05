import asyncio
from playwright.async_api import async_playwright

async def test_animate():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        await page.goto('https://www.meta.ai')
        
        # Submit prompt
        await page.evaluate("""(prompt) => {
            const textarea = document.querySelector('textarea[data-testid="composer-input"]');
            if (textarea) {
                textarea.value = prompt;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }""", 'A cat in space')
        await page.keyboard.press('Enter')
        
        # Wait for images
        await asyncio.sleep(15)
        
        # Get page info
        html = await page.content()
        with open("test_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # Look for image containers with Animate buttons
        containers = await page.query_selector_all('[data-testid="media"]')
        print(f"Media containers found: {len(containers)}")
        
        if containers:
            # Click first container/image
            await containers[0].click()
            await asyncio.sleep(3)
            print("Clicked first media container")
            
            # Take screenshot
            await page.screenshot(path="test_after_click.png")
            
            # Look for Animate button again
            buttons = await page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if text and 'Animate' in text:
                    print(f"Found Animate button: {text[:50]}")
                    # Try clicking with dispatchEvent
                    await btn.evaluate("b => { b.dispatchEvent(new MouseEvent('click', {bubbles: true})); }")
                    print("Clicked via dispatchEvent")
                    break
        
        await asyncio.sleep(10)
        
        # Check for video
        videos = await page.query_selector_all('video')
        print(f"Videos found: {len(videos)}")
        
        await page.screenshot(path="test_final.png")
        print("Saved test_final.png")
        
        await context.close()

asyncio.run(test_animate())
