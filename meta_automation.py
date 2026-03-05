import asyncio
from playwright.async_api import async_playwright

# CONFIGURATION
USER_DATA_DIR = "./meta_session"  # Folder to store login cookies
META_URL = "https://www.meta.ai"  # Main chat page (not /media)


async def generate_meta_video(prompt: str):
    async with async_playwright() as p:
        # Launch browser with persistent session (avoids repeated logins)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,  # Set to False the first time to log in manually
            args=["--disable-blink-features=AutomationControlled"]  # Anti-bot measure
        )
        page = await context.new_page()

        try:
            print(f"Opening Meta AI for prompt: {prompt}")
            await page.goto(META_URL)

            # Step 1: Type the prompt into the 'Describe your image' box
            # Selector targets the textarea with placeholder text as seen in your image
            textarea_selector = 'textarea[data-testid="composer-input"]'
            await page.wait_for_selector(textarea_selector, state="attached")
            # Use JavaScript to fill hidden textarea
            await page.evaluate(f"""(prompt) => {{
                const textarea = document.querySelector('textarea[data-testid="composer-input"]');
                textarea.value = prompt;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}""", prompt)

            # Step 2: Send the prompt
            await page.keyboard.press("Enter")
            
            # Wait for generation to start and images to appear
            print("Waiting for images to generate...")
            await asyncio.sleep(10)  # Give time for initial generation
            
            # Wait for image generation to complete (look for image elements)
            print("Waiting for image generation to complete...")
            try:
                # Look for generated images - they usually appear as img tags or in containers
                await page.wait_for_selector('img[src*="facebook"], img[src*="fbcdn"], [data-testid="media"]', timeout=60000)
                print("Images generated!")
            except:
                print("Warning: Could not confirm image generation, continuing...")

            # Step 3: Click 'Animate' button
            
            # Take screenshot to debug
            await page.screenshot(path="debug.png")
            print("Screenshot saved to debug.png")
            
            # Find assistant-message container and click Animate within it
            print("Looking for Animate button in assistant-message...")
            
            click_result = await page.evaluate("""() => {
                // Find the assistant message container
                const assistantMsg = document.querySelector('[data-testid="assistant-message"]');
                if (!assistantMsg) {
                    return 'no-assistant-message';
                }
                
                // Find Animate button within it - use trim to handle whitespace
                const buttons = Array.from(assistantMsg.querySelectorAll('button'));
                const animateBtn = buttons.find(b => b.textContent && b.textContent.trim().includes('Animate'));
                
                if (animateBtn) {
                    animateBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
                    // Try both click methods
                    animateBtn.click();
                    animateBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    return 'clicked-animate';
                }
                return 'no-animate-button';
            }""")
            print(f"Animate click result: {click_result}")

            # Step 4: Extract the final video URL
            print("Waiting for video to generate...")
            await asyncio.sleep(5)
            
            # Check URL - might have navigated
            current_url = page.url
            print(f"Current URL: {current_url}")
            
            # Take screenshot after animate
            await page.screenshot(path="debug_after_animate.png")
            print("Screenshot after animate saved")
            
            # Check for video elements
            videos = await page.query_selector_all('video')
            print(f"Video elements found: {len(videos)}")
            
            # Wait longer for video generation (can take 30-60 seconds)
            print("Waiting longer for video generation...")
            await asyncio.sleep(30)
            
            # Check again
            videos = await page.query_selector_all('video')
            print(f"Video elements after 30s: {len(videos)}")
            
            # Take another screenshot
            await page.screenshot(path="debug_after_30s.png")
            print("Screenshot after 30s saved")
            
            # We wait for the video tag to appear and get its source
            video_selector = 'video[src^="blob:"], video[src^="http"], video'
            await page.wait_for_selector(video_selector, timeout=90000)
            video_src = await page.get_attribute(video_selector, "src")

            print(f"Success! Video URL: {video_src}")
            return video_src

        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            await context.close()


if __name__ == "__main__":
    # Test run
    asyncio.run(generate_meta_video("A BMW car drifting on a snow road"))
