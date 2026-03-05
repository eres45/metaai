"""
Check a video prompt from history to see the interface.
"""
import asyncio
from playwright.async_api import async_playwright


async def check_video_prompt():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to one of the video prompts from history
        await page.goto("https://www.meta.ai/prompt/f3f87522-03d3-4ddf-abb4-c1470deded68")
        await asyncio.sleep(5)
        
        print(f"URL: {page.url}")
        
        # Get page text
        page_text = await page.evaluate("""() => document.body.innerText""")
        print("\n=== PAGE TEXT ===")
        lines = [l.strip() for l in page_text.split('\n') if l.strip()]
        for line in lines[:30]:
            print(f"  {line}")
        
        # Look for input
        textareas = await page.query_selector_all('textarea')
        print(f"\nFound {len(textareas)} textareas:")
        for ta in textareas:
            ph = await ta.get_attribute('placeholder')
            print(f"  - placeholder: {ph}")
        
        # Look for buttons
        buttons = await page.query_selector_all('button')
        print(f"\nButtons ({len(buttons)}):")
        for btn in buttons[:20]:
            text = await btn.text_content()
            if text:
                print(f"  - {text[:40]}")
        
        await page.screenshot(path="debug_video_prompt.png")
        await context.close()


asyncio.run(check_video_prompt())
