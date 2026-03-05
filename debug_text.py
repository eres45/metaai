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
                textarea.value = 'A cat dancing in the rain';
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }""")
        await page.keyboard.press('Enter')
        await asyncio.sleep(15)
        
        view_links = await page.query_selector_all('a[aria-label="View media"]')
        if view_links:
            await view_links[0].click()
            await asyncio.sleep(5)
            
            # Get full page text
            page_text = await page.evaluate("""() => document.body.innerText""")
            print("=== PAGE TEXT ===")
            print(page_text[:3000])
            print("=================\n")
            
            # Look for video-related text
            lines = page_text.split('\n')
            for line in lines:
                if 'video' in line.lower() or 'animate' in line.lower():
                    print(f"Found: {line}")
        
        await context.close()

asyncio.run(debug())
