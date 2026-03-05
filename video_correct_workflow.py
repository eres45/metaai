"""
Correct Video Generation Workflow:
1. Go to Create tab
2. Select "Create video" (not just Create)
3. Type prompt in video prompt box
4. Submit and wait 15-25 seconds
5. Get 4 videos
"""
import asyncio
import requests
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime


async def generate_video_correct():
    """Generate video using the correct workflow."""
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='./meta_session',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        try:
            # Step 1: Go to main page
            print("Step 1: Opening Meta AI...")
            await page.goto("https://www.meta.ai")
            await asyncio.sleep(3)
            print(f"  URL: {page.url}")
            
            # Step 2: Click Create in sidebar
            print("\nStep 2: Clicking Create...")
            create_link = await page.query_selector('a:has-text("Create")')
            if create_link:
                await create_link.click()
                await asyncio.sleep(3)
                print(f"  URL after Create: {page.url}")
                await page.screenshot(path="debug_step2_create.png")
            
            # Step 3: Look for and click "Create video"
            print("\nStep 3: Looking for 'Create video' button...")
            
            # Check for Create video button
            create_video_btn = None
            for selector in [
                'button:has-text("Create video")',
                'a:has-text("Create video")',
                '[data-testid] button:has-text("Create video")',
            ]:
                try:
                    create_video_btn = await page.wait_for_selector(selector, timeout=5000)
                    if create_video_btn:
                        print(f"  Found Create video with: {selector}")
                        break
                except:
                    continue
            
            if not create_video_btn:
                # Try JavaScript to find it
                print("  Trying JavaScript to find Create video...")
                result = await page.evaluate("""() => {
                    const buttons = Array.from(document.querySelectorAll('button, a'));
                    const btn = buttons.find(b => 
                        b.textContent && b.textContent.trim() === 'Create video'
                    );
                    if (btn) {
                        btn.click();
                        return 'clicked';
                    }
                    // List all buttons for debugging
                    const texts = buttons.map(b => b.textContent?.trim()).filter(t => t);
                    return { notFound: true, buttons: texts.slice(0, 20) };
                }""")
                print(f"  JS result: {result}")
                
                if result == 'clicked':
                    print("  ✅ Clicked Create video via JS")
                    await asyncio.sleep(3)
            else:
                await create_video_btn.click()
                print("  ✅ Clicked Create video button")
                await asyncio.sleep(3)
            
            print(f"  URL after Create video: {page.url}")
            await page.screenshot(path="debug_step3_video_interface.png")
            
            # Step 4: Look for video prompt input
            print("\nStep 4: Looking for video prompt input...")
            
            # Find the prompt textarea for video
            prompt_input = None
            for selector in [
                'textarea[placeholder*="video" i]',
                'textarea[placeholder*="describe" i]',
                'textarea[data-testid="composer-input"]',
                'textarea',
            ]:
                try:
                    prompt_input = await page.wait_for_selector(selector, timeout=5000)
                    if prompt_input:
                        placeholder = await prompt_input.get_attribute('placeholder')
                        print(f"  Found input: {selector} (placeholder: {placeholder})")
                        break
                except:
                    continue
            
            if not prompt_input:
                print("  ❌ Could not find prompt input")
                return {"success": False, "error": "No prompt input found"}
            
            # Step 5: Type prompt
            prompt = "A cat dancing"
            print(f"\nStep 5: Typing prompt: '{prompt}'")
            await prompt_input.fill(prompt)
            await asyncio.sleep(1)
            
            # Step 6: Submit (look for generate button or press Enter)
            print("\nStep 6: Submitting prompt...")
            
            # Look for generate/create button
            generate_btn = await page.query_selector('button:has-text("Generate"), button:has-text("Create"), button[type="submit"]')
            if generate_btn:
                await generate_btn.click()
                print("  ✅ Clicked Generate button")
            else:
                await page.keyboard.press("Enter")
                print("  ✅ Pressed Enter")
            
            await asyncio.sleep(3)
            print(f"  URL after submit: {page.url}")
            await page.screenshot(path="debug_step6_after_submit.png")
            
            # Step 7: Wait 15-25 seconds for generation
            print("\nStep 7: Waiting 15-25 seconds for video generation...")
            
            video_urls = []
            for i in range(5):  # Check every 5 seconds for 25 seconds total
                await asyncio.sleep(5)
                print(f"  [{i+1}/5] Checking for videos after {(i+1)*5}s...")
                
                # Check for video elements
                videos = await page.query_selector_all('video[src*="fbcdn"], video[src*="video-sin"]')
                
                if videos:
                    print(f"    🎉 Found {len(videos)} videos!")
                    for vid in videos:
                        src = await vid.get_attribute('src')
                        if src and src not in video_urls:
                            video_urls.append(src)
                            print(f"      URL: {src[:70]}...")
                    
                    if len(video_urls) >= 4:
                        print("    ✅ Got all 4 videos!")
                        break
                else:
                    # Also check all video tags
                    all_vids = await page.query_selector_all('video')
                    print(f"    Total video elements: {len(all_vids)}")
                    
                    for vid in all_vids:
                        src = await vid.get_attribute('src')
                        if src and ('fbcdn' in src or 'video' in src.lower()):
                            if src not in video_urls:
                                video_urls.append(src)
                                print(f"    🎉 Video found: {src[:70]}...")
            
            # Step 8: Click Animate if needed
            if len(video_urls) < 4:
                print("\nStep 8: Looking for Animate button...")
                
                animate_btn = await page.query_selector('button:has-text("Animate")')
                if animate_btn:
                    print("  ✅ Found Animate, clicking...")
                    await animate_btn.click(force=True)
                    await asyncio.sleep(2)
                    
                    # Check for Custom animate
                    custom = await page.query_selector('button:has-text("Custom animate")')
                    if custom:
                        await custom.click()
                        print("  ✅ Clicked Custom animate")
                        await asyncio.sleep(2)
                    
                    # Wait more
                    print("  Waiting 20 more seconds...")
                    for i in range(4):
                        await asyncio.sleep(5)
                        
                        videos = await page.query_selector_all('video[src*="fbcdn"], video[src*="video-sin"]')
                        if videos:
                            print(f"    [{i+1}] Found {len(videos)} videos")
                            for vid in videos:
                                src = await vid.get_attribute('src')
                                if src and src not in video_urls:
                                    video_urls.append(src)
                                    print(f"      URL: {src[:70]}...")
                        
                        if len(video_urls) >= 4:
                            break
            
            await page.screenshot(path="debug_final_videos.png")
            
            # Step 9: Download videos
            print(f"\nStep 9: Downloading {len(video_urls)} videos...")
            
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
    print("Correct Video Generation Workflow")
    print("="*80)
    
    result = asyncio.run(generate_video_correct())
    
    print("\n" + "="*80)
    print("RESULT:")
    print(f"  Success: {result.get('success')}")
    print(f"  Videos: {result.get('count')}")
    print(f"  Downloaded: {len(result.get('downloaded_files', []))}")
    print("="*80)
