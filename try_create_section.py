"""
Try the Create section workflow for video generation.
"""
import asyncio
from playwright.async_api import async_playwright


async def try_create_section():
    """Try using the Create section for video generation."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        print("Step 1: Go to main page and find Create...")
        await page.goto("https://www.meta.ai")
        await asyncio.sleep(3)
        
        # Look for Create in sidebar
        create_link = await page.query_selector('a:has-text("Create")')
        if create_link:
            text = await create_link.text_content()
            href = await create_link.get_attribute('href')
            print(f"  Found Create: '{text}' -> {href}")
            
            print("\nStep 2: Click Create...")
            await create_link.click()
            await asyncio.sleep(5)
            
            print(f"  URL after Create: {page.url}")
            await page.screenshot(path="debug_create_section.png")
            
            # Look for video/image options
            print("\nStep 3: Looking for video options...")
            
            # Check all buttons and links
            buttons = await page.query_selector_all('button, a')
            print(f"  Found {len(buttons)} clickable elements")
            
            for btn in buttons[:30]:
                text = await btn.text_content()
                href = await btn.get_attribute('href')
                if text and any(word in text.lower() for word in ['video', 'image', 'create', 'generate']):
                    print(f"    - '{text.strip()[:40]}' (href: {href})")
            
            # Look for specific text
            page_text = await page.evaluate("""() => document.body.innerText""")
            
            # Check for video creation option
            if 'create video' in page_text.lower() or 'video' in page_text.lower():
                print("\n  ✅ Video-related text found!")
                lines = [l.strip() for l in page_text.split('\n') 
                        if 'video' in l.lower() or 'create' in l.lower()]
                for line in lines[:10]:
                    print(f"    {line}")
            
            # Look for prompt input
            inputs = await page.query_selector_all('textarea, input[type="text"]')
            print(f"\n  Found {len(inputs)} input fields:")
            for inp in inputs:
                ph = await inp.get_attribute('placeholder')
                testid = await inp.get_attribute('data-testid')
                print(f"    - placeholder: '{ph}', testid: {testid}")
        else:
            print("  ❌ Create link not found")
        
        await context.close()


if __name__ == "__main__":
    print("="*80)
    print("Create Section Workflow")
    print("="*80)
    asyncio.run(try_create_section())
