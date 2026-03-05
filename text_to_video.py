"""
Text-to-Video generation on /media page - Based on Auto Meta extension workflow.
Extension: https://chromewebstore.google.com/detail/auto-meta-automation-for/bjlfjfeoocgddchhmnadaanmejgglaag?pli=1

Mode: Text-to-Video (no images selected)
Workflow:
1. Go to https://www.meta.ai/media
2. Make sure no images are selected (Selected: 0)
3. Enter prompt
4. Submit and wait 15-30 seconds
5. Get 4 videos
"""
import asyncio
import requests
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime


async def text_to_video():
    """Generate video using text-to-video mode on /media page."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to /media page
            print("Step 1: Navigating to /media page...")
            await page.goto("https://www.meta.ai/media")
            await asyncio.sleep(5)  # Wait for page to fully load
            print(f"  URL: {page.url}")
            await page.screenshot(path="debug_step1_media_page.png")
            
            # Step 2: Check if any images are selected and deselect them
            print("\nStep 2: Ensuring no images selected (Text-to-Video mode)...")
            
            # Look for "Selected: X" text or any selected indicator
            selected_count = await page.evaluate("""() => {
                const text = document.body.innerText;
                const match = text.match(/Selected:\s*(\d+)/);
                return match ? parseInt(match[1]) : 0;
            }""")
            print(f"  Currently selected: {selected_count} images")
            
            # If images are selected, we need to deselect them
            if selected_count > 0:
                print("  Deselecting images...")
                # Click somewhere neutral or find a clear selection button
                await page.evaluate("""() => {
                    // Try to click on empty area or clear button
                    const clearBtn = Array.from(document.querySelectorAll('button')).find(
                        b => b.textContent && b.textContent.includes('Clear')
                    );
                    if (clearBtn) clearBtn.click();
                }""")
                await asyncio.sleep(2)
            
            # Step 3: Look for prompt input (Text-to-Video interface)
            print("\nStep 3: Looking for video prompt input...")
            
            # On /media page with no images selected, there should be a prompt input
            # Let's check various possible selectors
            prompt_input = None
            
            # Method 1: Look for textarea with specific placeholders
            for selector in [
                'textarea[placeholder*="video" i]',
                'textarea[placeholder*="describe" i]',
                'textarea[placeholder*="imagine" i]',
                'textarea[placeholder*="prompt" i]',
                'textarea[data-testid="composer-input"]',
                'textarea',
            ]:
                try:
                    prompt_input = await page.wait_for_selector(selector, timeout=3000)
                    if prompt_input:
                        placeholder = await prompt_input.get_attribute('placeholder')
                        print(f"  ✅ Found input: {selector}")
                        print(f"     Placeholder: '{placeholder}'")
                        break
                except:
                    continue
            
            if not prompt_input:
                # Method 2: Look for any input field that might be for prompts
                print("  Trying alternative methods...")
                all_inputs = await page.query_selector_all('textarea, input[type="text"]')
                print(f"     Total inputs found: {len(all_inputs)}")
                
                for i, inp in enumerate(all_inputs):
                    try:
                        ph = await inp.get_attribute('placeholder')
                        testid = await inp.get_attribute('data-testid')
                        print(f"     Input {i}: placeholder='{ph}', testid='{testid}'")
                        
                        # Use the one with a placeholder that suggests text input
                        if ph and any(word in ph.lower() for word in ['describe', 'video', 'imagine', 'ask', 'prompt']):
                            prompt_input = inp
                            print(f"     -> Selected input {i}")
                            break
                    except:
                        pass
            
            if not prompt_input:
                print("  ❌ Could not find prompt input")
                return {"success": False, "error": "No prompt input found on /media page"}
            
            # Step 4: Enter prompt using JavaScript (element may be hidden)
            prompt = "A cat playing piano in a jazz club"
            print(f"\nStep 4: Entering prompt: '{prompt}'")
            await page.evaluate("""(prompt) => {
                const ta = document.querySelector('textarea[data-testid="composer-input"]');
                if (ta) {
                    ta.value = prompt;
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""", prompt)
            await asyncio.sleep(1)
            
            # Step 5: Submit using JavaScript or keyboard
            print("\nStep 5: Submitting...")
            
            # Use keyboard press (more reliable)
            await page.keyboard.press("Enter")
            print("  ✅ Pressed Enter to submit")
            
            await asyncio.sleep(3)
            print(f"  URL after submit: {page.url}")
            await page.screenshot(path="debug_step5_after_submit.png")
            
            # Step 6: Wait 15-30 seconds for video generation
            print("\nStep 6: Waiting for video generation (15-30s)...")
            
            video_urls = []
            
            # Poll every 3 seconds for 30 seconds
            for i in range(10):
                await asyncio.sleep(3)
                elapsed = (i + 1) * 3
                
                # Check for video elements with fbcdn URLs
                videos = await page.query_selector_all('video[src*="fbcdn.net"], video[src*="video-sin"]')
                
                if videos:
                    print(f"  [{elapsed}s] 🎉 Found {len(videos)} videos!")
                    
                    for vid in videos:
                        src = await vid.get_attribute('src')
                        if src and src not in video_urls:
                            video_urls.append(src)
                            print(f"      URL: {src[:70]}...")
                    
                    if len(video_urls) >= 4:
                        print(f"  ✅ Got all 4 videos!")
                        break
                else:
                    # Also check for any video elements
                    all_vids = await page.query_selector_all('video')
                    if all_vids and elapsed % 6 == 0:
                        print(f"  [{elapsed}s] {len(all_vids)} video elements (checking for URLs)...")
            
            # Step 7: Download videos
            print(f"\nStep 7: Downloading {len(video_urls)} videos...")
            
            Path("downloads/videos").mkdir(parents=True, exist_ok=True)
            downloaded = []
            
            for i, url in enumerate(video_urls[:4]):
                print(f"  Downloading video {i+1}...")
                try:
                    response = requests.get(url, stream=True, timeout=120)
                    if response.status_code == 200:
                        filepath = f"downloads/videos/video_{i+1}_{datetime.now().strftime('%H%M%S')}.mp4"
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"    ✅ Saved: {filepath}")
                        downloaded.append(filepath)
                    else:
                        print(f"    ❌ HTTP {response.status_code}")
                except Exception as e:
                    print(f"    ❌ Error: {e}")
            
            await page.screenshot(path="debug_step7_final.png")
            await context.close()
            
            return {
                "success": len(video_urls) > 0,
                "prompt": prompt,
                "video_urls": video_urls,
                "downloaded_files": downloaded,
                "count": len(video_urls)
            }
            
        except Exception as e:
            await context.close()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("="*80)
    print("Text-to-Video Generation on /media")
    print("Based on Auto Meta extension workflow")
    print("="*80)
    
    result = asyncio.run(text_to_video())
    
    print("\n" + "="*80)
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Videos found: {result.get('count')}")
    print(f"  Downloaded: {len(result.get('downloaded_files', []))}")
    print("="*80)
