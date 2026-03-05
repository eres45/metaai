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
            
            # Get page HTML before clicking
            html_before = await page.content()
            with open("create_page_before.html", "w", encoding="utf-8") as f:
                f.write(html_before[:5000])
            
            # Click Animate and monitor for changes
            print("Clicking Animate...")
            
            # Try to find what happens - look for network or DOM changes
            await page.evaluate("""() => {
                // Log all clicks
                document.addEventListener('click', (e) => {
                    console.log('Clicked:', e.target.tagName, e.target.textContent?.substring(0, 50));
                }, {once: true});
                
                const btn = Array.from(document.querySelectorAll('button')).find(b => 
                    b.textContent && b.textContent.includes('Animate'));
                if (btn) {
                    btn.click();
                    return 'clicked';
                }
                return 'not-found';
            }""")
            
            await asyncio.sleep(5)
            
            # Check if there's a form, input, or any change
            html_after = await page.content()
            with open("create_page_after.html", "w", encoding="utf-8") as f:
                f.write(html_after[:5000])
            
            print(f"HTML length before: {len(html_before)}")
            print(f"HTML length after: {len(html_after)}")
            
            # Look for any new buttons or inputs
            buttons = await page.query_selector_all('button')
            print(f"\nButtons after click ({len(buttons)}):")
            for btn in buttons:
                text = await btn.text_content()
                if text:
                    print(f"  - {text[:50]}")
        
        await context.close()

asyncio.run(debug())
