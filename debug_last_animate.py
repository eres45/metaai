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
        
        # Click View media
        view_links = await page.query_selector_all('a[aria-label="View media"]')
        if view_links:
            await view_links[0].click()
            await asyncio.sleep(5)
            
            # Get all button info before clicking
            buttons_before = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button')).map(b => ({
                    text: b.textContent?.trim(),
                    hasClick: b.onclick !== null
                }));
            }""")
            print(f"Total buttons before: {len(buttons_before)}")
            
            # Click the last "Animate" button (likely the generate button)
            await page.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const animateButtons = buttons.filter(b => 
                    b.textContent && b.textContent.includes('Animate'));
                
                console.log('Animate buttons found:', animateButtons.length);
                
                // Click the last one (index -1)
                if (animateButtons.length > 0) {
                    const lastBtn = animateButtons[animateButtons.length - 1];
                    lastBtn.scrollIntoView({block: 'center'});
                    lastBtn.click();
                    lastBtn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    return 'clicked-last-animate';
                }
                return 'no-animate-buttons';
            }""")
            
            print("Clicked, waiting...")
            await asyncio.sleep(30)
            
            # Check for video
            videos = await page.query_selector_all('video')
            print(f"Videos found: {len(videos)}")
            
            # Check page URL
            print(f"Current URL: {page.url}")
            
            # Look for any video-related text
            page_text = await page.evaluate("""() => document.body.innerText""")
            if 'video' in page_text.lower():
                print("Page contains 'video' text")
            
            await page.screenshot(path="debug_last_animate.png")
        
        await context.close()

asyncio.run(debug())
