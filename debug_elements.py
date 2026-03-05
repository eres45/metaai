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
                textarea.value = prompt;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }""", 'A cat in space')
        await page.keyboard.press('Enter')
        await asyncio.sleep(15)
        
        # Get all data-testid elements
        elements = await page.query_selector_all('[data-testid]')
        print('Data-testid elements:')
        for el in elements[:40]:
            testid = await el.get_attribute('data-testid')
            tag = await el.evaluate('e => e.tagName')
            text = await el.text_content()
            text_preview = text[:30].replace('\n', ' ') if text else ''
            print(f'  {tag}: {testid} - {text_preview}')
        
        await context.close()

asyncio.run(debug())
