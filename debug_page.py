import asyncio
from playwright.async_api import async_playwright

async def check_page():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        await page.goto('https://www.meta.ai')
        
        # Fill and submit prompt
        await page.evaluate("""(prompt) => {
            const textarea = document.querySelector('textarea[data-testid="composer-input"]');
            if (textarea) {
                textarea.value = prompt;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }""", 'A cat in space')
        await page.keyboard.press('Enter')
        
        # Wait for generation
        await asyncio.sleep(15)
        
        # Get all buttons
        buttons = await page.query_selector_all('button')
        print('Buttons found:')
        for btn in buttons[:30]:
            text = await btn.text_content()
            if text and text.strip():
                print(f'  - {text.strip()[:50]}')
        
        # Get all images
        images = await page.query_selector_all('img')
        print(f'\nImages found: {len(images)}')
        for img in images[:5]:
            src = await img.get_attribute('src')
            print(f'  - {src[:80] if src else "no src"}...')
        
        # Save screenshot
        await page.screenshot(path='debug2.png')
        print('\nScreenshot saved to debug2.png')
        
        await context.close()

asyncio.run(check_page())
