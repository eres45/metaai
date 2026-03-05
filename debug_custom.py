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
            
            # Click Animate to open custom animate
            await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.textContent && b.textContent.includes('Animate') && !b.textContent.includes('Custom'));
                if (btn) {
                    btn.click();
                    return 'clicked';
                }
                return 'not-found';
            }""")
            
            await asyncio.sleep(3)
            
            # Click Custom animate
            custom_btn = await page.query_selector('button:has-text("Custom animate")')
            if custom_btn:
                print("Found Custom animate button")
                await custom_btn.click()
                await asyncio.sleep(5)
                
                await page.screenshot(path="debug_custom_animate.png")
                
                # Look for input field or generate button
                inputs = await page.query_selector_all('input, textarea')
                print(f"Inputs found: {len(inputs)}")
                
                buttons = await page.query_selector_all('button')
                print(f"\nButtons ({len(buttons)}):")
                for btn in buttons:
                    text = await btn.text_content()
                    if text:
                        print(f"  - {text[:50]}")
        
        await context.close()

asyncio.run(debug())
