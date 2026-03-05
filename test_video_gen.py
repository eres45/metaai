"""
Test video generation with proper prompt format.
"""
import asyncio
from playwright.async_api import async_playwright


async def test_video_gen():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True
        )
        page = await context.new_page()
        
        # Go to a video prompt page
        await page.goto("https://www.meta.ai/prompt/f3f87522-03d3-4ddf-abb4-c1470deded68")
        await asyncio.sleep(3)
        
        print(f"URL: {page.url}")
        
        # Submit a video prompt
        video_prompt = "Generate a video: A dog playing fetch in a park"
        print(f"Sending: {video_prompt}")
        
        await page.evaluate("""(prompt) => {
            const ta = document.querySelector('textarea[data-testid="composer-input"]');
            if (ta) {
                ta.value = prompt;
                ta.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }""", video_prompt)
        
        await page.keyboard.press("Enter")
        print("Submitted, waiting...")
        
        # Wait and check
        for i in range(20):
            await asyncio.sleep(5)
            
            # Check for videos
            videos = await page.query_selector_all('video')
            if videos:
                print(f"🎬 Found {len(videos)} videos after {(i+1)*5}s")
                for v in videos:
                    src = await v.get_attribute('src')
                    print(f"  URL: {src[:60]}...")
                break
            
            if (i+1) % 6 == 0:
                print(f"  Still waiting... ({(i+1)*5}s)")
        
        await page.screenshot(path="debug_video_test.png")
        await context.close()


asyncio.run(test_video_gen())
