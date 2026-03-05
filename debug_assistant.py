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
        
        print(f"URL: {page.url}")
        
        # Get assistant-message HTML
        assistant_html = await page.evaluate("""() => {
            const assistantMsg = document.querySelector('[data-testid="assistant-message"]');
            if (assistantMsg) {
                return {
                    found: true,
                    html: assistantMsg.outerHTML.substring(0, 2000),
                    buttons: Array.from(assistantMsg.querySelectorAll('button')).map(b => ({
                        text: b.textContent,
                        class: b.className
                    }))
                };
            }
            return { found: false };
        }""")
        
        print(f"Assistant message found: {assistant_html.get('found')}")
        if assistant_html.get('found'):
            print(f"Buttons: {assistant_html.get('buttons')}")
            print(f"HTML snippet: {assistant_html.get('html')[:500]}")
        
        # Also check all buttons on page
        all_buttons = await page.query_selector_all('button')
        print(f"\nAll buttons ({len(all_buttons)}):")
        for btn in all_buttons:
            text = await btn.text_content()
            if text and 'Animate' in text:
                print(f"  - Animate button: {text[:50]}")
                # Check parent
                parent_testid = await btn.evaluate("""b => {
                    let el = b.parentElement;
                    while (el && !el.getAttribute('data-testid')) {
                        el = el.parentElement;
                    }
                    return el ? el.getAttribute('data-testid') : 'no-testid';
                }""")
                print(f"    Parent testid: {parent_testid}")
        
        await page.screenshot(path="debug_assistant.png")
        await context.close()

asyncio.run(debug())
