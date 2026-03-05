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
        
        print(f"Before click URL: {page.url}")
        
        # Click first Animate button
        result = await page.evaluate("""() => {
            const assistantMsg = document.querySelector('[data-testid="assistant-message"]');
            if (!assistantMsg) return 'no-assistant-message';
            
            const buttons = Array.from(assistantMsg.querySelectorAll('button'));
            const animateBtn = buttons.find(b => b.textContent && b.textContent.trim().includes('Animate'));
            
            if (animateBtn) {
                animateBtn.click();
                return 'clicked';
            }
            return 'not-found';
        }""")
        print(f"Click result: {result}")
        
        # Wait and check for changes
        await asyncio.sleep(5)
        print(f"After 5s URL: {page.url}")
        
        # Check for any video-related elements
        elements = await page.query_selector_all('video, [data-testid*="video"], .video, [class*="video"]')
        print(f"Video-related elements: {len(elements)}")
        
        # Check for any changes in assistant-message
        msg = await page.query_selector('[data-testid="assistant-message"]')
        if msg:
            text = await msg.text_content()
            print(f"Assistant message text preview: {text[:200]}...")
        
        await page.screenshot(path="debug_click_result.png")
        
        # Wait longer
        await asyncio.sleep(20)
        print(f"After 25s URL: {page.url}")
        
        # Check again
        videos = await page.query_selector_all('video')
        print(f"Videos after 25s: {len(videos)}")
        
        await page.screenshot(path="debug_final.png")
        
        await context.close()

asyncio.run(debug())
