"""
Check if clicking "Image" button at bottom toggles to Video mode.
"""
import asyncio
from playwright.async_api import async_playwright


async def check_image_button():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to Create page
        await page.goto("https://www.meta.ai/media")
        await asyncio.sleep(5)
        
        print("Looking for Image button...")
        
        # Find Image button
        buttons = await page.query_selector_all('button')
        for i, btn in enumerate(buttons):
            text = await btn.text_content()
            if text and text.strip() == 'Image':
                print(f"Found Image button at index {i}")
                
                # Click it
                await btn.click()
                print("Clicked Image button")
                await asyncio.sleep(3)
                
                # Check what changed
                page_text = await page.evaluate("""() => document.body.innerText""")
                print("\n=== AFTER CLICKING IMAGE ===")
                lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                for line in lines[:20]:
                    print(f"  {line}")
                
                # Look for Video option
                if 'video' in page_text.lower():
                    print("\n  ✅ 'Video' text found!")
                    video_lines = [l for l in lines if 'video' in l.lower()]
                    for vl in video_lines[:5]:
                        print(f"    - {vl}")
                
                # Check for input
                inputs = await page.query_selector_all('textarea, input')
                print(f"\n  Input fields: {len(inputs)}")
                for inp in inputs:
                    ph = await inp.get_attribute('placeholder')
                    print(f"    - {ph}")
                
                await page.screenshot(path="debug_after_image_click.png")
                break
        else:
            print("Image button not found")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Checking Image Button")
    print("="*80)
    asyncio.run(check_image_button())
