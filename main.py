from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from complete_service import get_service, MetaGenerationService
import asyncio
import os
import json

app = FastAPI(title="Meta AI Generation API")

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify ["https://www.waspai.in"])
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

task_db = {}  # Task status storage

# Initialize service
service = get_service()


@app.post("/generate/images")
async def generate_images(
    prompt: str = Query(..., description="Image generation prompt"),
    num_images: int = Query(4, ge=1, le=4, description="Number of images"),
    download: bool = Query(True, description="Download images to server")
):
    """Generate images from text prompt."""
    task_id = f"img_{hash(prompt + str(num_images)) % 10000000}"
    
    if download:
        result = await service.generate_and_download_images(
            prompt=prompt,
            num_images=num_images
        )
    else:
        result = await service.generate_images(
            prompt=prompt,
            num_images=num_images
        )
    
    task_db[task_id] = {
        "type": "images",
        "status": "completed" if result.get("success") else "failed",
        "result": result
    }
    
    return {
        "task_id": task_id,
        "success": result.get("success"),
        "prompt": prompt,
        "image_urls": result.get("image_urls", []),
        "downloaded_files": result.get("downloaded_files", []),
        "download_dir": result.get("download_dir")
    }


@app.post("/generate/images/async")
async def generate_images_async(
    prompt: str = Query(..., description="Image generation prompt"),
    num_images: int = Query(4, ge=1, le=4),
    background_tasks: BackgroundTasks = None
):
    """Generate images asynchronously (non-blocking)."""
    task_id = f"img_async_{hash(prompt + str(num_images)) % 10000000}"
    task_db[task_id] = {"type": "images", "status": "processing"}
    
    background_tasks.add_task(
        process_image_task, 
        task_id, 
        prompt, 
        num_images
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Image generation started",
        "check_status_url": f"/check-status/{task_id}"
    }


async def process_image_task(task_id: str, prompt: str, num_images: int):
    """Process image generation in background."""
    result = await service.generate_and_download_images(
        prompt=prompt,
        num_images=num_images
    )
    
    task_db[task_id] = {
        "type": "images",
        "status": "completed" if result.get("success") else "failed",
        "result": result
    }


@app.post("/generate/video")
async def generate_video(
    prompt: str = Query(..., description="Video generation prompt"),
    download: bool = Query(True, description="Download videos to server")
):
    """Generate video using working Text-to-Video method."""
    task_id = f"vid_{hash(prompt)} % 10000000"
    
    if download:
        result = await service.generate_and_download_video_v2(prompt=prompt)
    else:
        result = await service.generate_video_v2(prompt=prompt)
    
    task_db[task_id] = {
        "type": "video",
        "status": "completed" if result.get("success") else "failed",
        "result": result
    }
    
    return {
        "task_id": task_id,
        "success": result.get("success"),
        "prompt": prompt,
        "video_urls": result.get("video_urls", []),
        "downloaded_files": result.get("downloaded_files", []),
        "download_dir": result.get("download_dir")
    }


@app.post("/generate/video/async")
async def generate_video_async(
    prompt: str = Query(..., description="Video generation prompt"),
    background_tasks: BackgroundTasks = None
):
    """Generate video asynchronously (non-blocking)."""
    task_id = f"vid_async_{hash(prompt) % 10000000}"
    task_db[task_id] = {"type": "video", "status": "processing"}
    
    background_tasks.add_task(
        process_video_task,
        task_id,
        prompt
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Video generation started",
        "check_status_url": f"/check-status/{task_id}"
    }


async def process_video_task(task_id: str, prompt: str):
    """Process video generation in background."""
    result = await service.generate_and_download_video_v2(prompt=prompt)
    
    task_db[task_id] = {
        "type": "video",
        "status": "completed" if result.get("success") else "failed",
        "result": result
    }


@app.get("/list-downloads")
async def list_downloads():
    """List all downloaded files."""
    from pathlib import Path
    downloads = {"images": [], "videos": []}
    
    img_dir = Path("downloads/images")
    vid_dir = Path("downloads/videos")
    
    if img_dir.exists():
        downloads["images"] = [str(f) for f in img_dir.glob("*") if f.is_file()]
    
    if vid_dir.exists():
        downloads["videos"] = [str(f) for f in vid_dir.glob("*") if f.is_file()]
    
    return downloads


@app.get("/check-status/{task_id}")
async def check_status(task_id: str):
    """Check task status and results."""
    task = task_db.get(task_id)
    if not task:
        return {"status": "not_found", "task_id": task_id}
    
    return {
        "task_id": task_id,
        "type": task.get("type"),
        "status": task.get("status"),
        "result": task.get("result") if task.get("status") == "completed" else None
    }


@app.get("/download/{task_id}/{file_index}")
async def download_file(task_id: str, file_index: int):
    """Download a generated file by task ID and index."""
    task = task_db.get(task_id)
    if not task or task.get("status") != "completed":
        return {"error": "Task not found or not completed"}
    
    result = task.get("result", {})
    files = result.get("downloaded_files", [])
    
    if file_index < 0 or file_index >= len(files):
        return {"error": "File index out of range"}
    
    filepath = files[file_index]
    if os.path.exists(filepath):
        return FileResponse(
            filepath,
            media_type="application/octet-stream",
            filename=os.path.basename(filepath)
        )
    else:
        return {"error": "File not found"}


@app.get("/generate/video/v2")
@app.post("/generate/video/v2")
async def generate_video_v2_direct(
    prompt: str = Query(..., description="Video generation prompt")
):
    """Generate video using working code from debug endpoint."""
    from playwright.async_api import async_playwright
    import asyncio
    import re
    
    result = {
        "steps": [],
        "video_urls": [],
        "page_info": {}
    }
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="./meta_session",
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Load cookies
            storage_json = os.environ.get("STORAGE_STATE")
            if storage_json:
                storage_state = json.loads(storage_json)
                await context.add_cookies(storage_state.get("cookies", []))
                result["steps"].append(f"Loaded {len(storage_state.get('cookies', []))} cookies")
            
            page = await context.new_page()
            
            # Navigate
            await page.goto("https://www.meta.ai", timeout=30000)
            await asyncio.sleep(3)
            result["steps"].append(f"Navigated to {page.url}")
            
            # Check login
            page_text = await page.evaluate("() => document.body.innerText.slice(0, 300)")
            result["page_info"]["is_logged_in"] = "log in" not in page_text.lower()
            result["steps"].append(f"Logged in: {result['page_info']['is_logged_in']}")
            
            # Submit prompt
            video_prompt = f"Generate a video: {prompt}"
            await page.evaluate("""(prompt) => {
                const ta = document.querySelector('textarea[data-testid="composer-input"]');
                if (ta) {
                    ta.value = prompt;
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""", video_prompt)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            result["steps"].append("Prompt submitted")
            start_time = asyncio.get_event_loop().time()
            
            # POLLING: Check every 3 seconds, max 90 seconds, exit early when found
            result["steps"].append("Polling for videos (max 90s, checking every 3s)...")
            max_wait = 90
            check_interval = 3
            min_wait = 15  # Minimum wait before checking (generation takes time)
            
            # Initial minimum wait
            await asyncio.sleep(min_wait)
            elapsed = min_wait
            
            while elapsed < max_wait:
                # Check for videos in HTML
                page_html = await page.content()
                mp4_matches = re.findall(r'https://[^"\s<>]*\.mp4[^"\s<>]*', page_html)
                
                if mp4_matches:
                    result["steps"].append(f"[{elapsed}s] Found {len(mp4_matches)} .mp4 URLs in HTML")
                    for url in mp4_matches[:5]:
                        clean_url = url.replace('&amp;', '&')
                        if clean_url not in result["video_urls"]:
                            result["video_urls"].append(clean_url)
                            result["steps"].append(f"Found: {clean_url[:60]}...")
                    
                    # Exit early if we have videos
                    if len(result["video_urls"]) >= 3:
                        result["steps"].append(f"[{elapsed}s] Found 3+ videos, exiting early!")
                        break
                
                # Also check video elements
                videos = await page.query_selector_all('video')
                if videos:
                    result["page_info"]["video_elements_count"] = len(videos)
                    for vid in videos[:3]:
                        src = await vid.get_attribute('src')
                        if src and '.mp4' in src and src not in result["video_urls"]:
                            result["video_urls"].append(src)
                            result["steps"].append(f"Found video element: {src[:60]}...")
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                
                # Log progress every 15 seconds
                if elapsed % 15 == 0:
                    result["steps"].append(f"[{elapsed}s] Still polling...")
            
            result["total_elapsed_time"] = elapsed
            result["page_info"]["final_url"] = page.url
            result["page_info"]["mp4_matches_in_html"] = len(result["video_urls"])
            
            await context.close()
            result["success"] = len(result["video_urls"]) > 0
            result["steps"].append(f"Done in {elapsed}s. Total videos: {len(result['video_urls'])}")
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
    
    return result


@app.get("/debug/video-simple")
async def debug_video_simple(prompt: str = "A cat playing piano"):
    """Simple debug: Focus on video URL extraction only."""
    from playwright.async_api import async_playwright
    import asyncio
    import re
    
    result = {
        "steps": [],
        "video_urls": [],
        "page_info": {}
    }
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="./meta_session",
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Load cookies
            storage_json = os.environ.get("STORAGE_STATE")
            if storage_json:
                storage_state = json.loads(storage_json)
                await context.add_cookies(storage_state.get("cookies", []))
                result["steps"].append(f"Loaded {len(storage_state.get('cookies', []))} cookies")
            
            page = await context.new_page()
            
            # Navigate
            await page.goto("https://www.meta.ai", timeout=30000)
            await asyncio.sleep(3)
            result["steps"].append(f"Navigated to {page.url}")
            
            # Check login
            page_text = await page.evaluate("() => document.body.innerText.slice(0, 300)")
            result["page_info"]["is_logged_in"] = "log in" not in page_text.lower()
            result["steps"].append(f"Logged in: {result['page_info']['is_logged_in']}")
            
            # Submit prompt
            video_prompt = f"Generate a video: {prompt}"
            await page.evaluate("""(prompt) => {
                const ta = document.querySelector('textarea[data-testid="composer-input"]');
                if (ta) {
                    ta.value = prompt;
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }""", video_prompt)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            result["steps"].append("Prompt submitted")
            
            # POLLING: Check every 2 seconds, max 60 seconds, exit early when found
            result["steps"].append("Polling for images (max 60s, checking every 2s)...")
            max_wait = 60
            check_interval = 2
            min_wait = 8  # Minimum wait before checking (generation takes time)
            image_urls = []
            
            # Initial minimum wait
            await asyncio.sleep(min_wait)
            elapsed = min_wait
            
            while elapsed < max_wait:
                # Extract from HTML - most reliable method
                page_html = await page.content()
                
                # Check for fbcdn image URLs in HTML
                fbcdn_matches = re.findall(r'https://[^"\s<>]*fbcdn\.net[^"\s<>]*\.(?:jpg|jpeg|png|webp)[^"\s<>]*', page_html)
                
                if fbcdn_matches:
                    result["steps"].append(f"[{elapsed}s] Found {len(fbcdn_matches)} fbcdn URLs in HTML")
                    for url in fbcdn_matches[:num_images]:
                        clean_url = url.replace('&amp;', '&')
                        if clean_url not in image_urls:
                            image_urls.append(clean_url)
                            result["steps"].append(f"Found: {clean_url[:60]}...")
                    
                    # Exit early if we have enough images
                    if len(image_urls) >= num_images:
                        result["steps"].append(f"[{elapsed}s] Found {num_images}+ images, exiting early!")
                        break
                
                # Also check image elements
                images = await page.query_selector_all('img[src*="fbcdn.net"]')
                if images:
                    for img in images[:num_images]:
                        src = await img.get_attribute('src')
                        if src and src not in image_urls:
                            image_urls.append(src)
                            result["steps"].append(f"Found img element: {src[:60]}...")
                    
                    if len(image_urls) >= num_images:
                        break
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                
                # Log progress every 10 seconds
                if elapsed % 10 == 0:
                    result["steps"].append(f"[{elapsed}s] Still polling...")
            
            result["image_urls"] = image_urls[:num_images]
            result["total_elapsed_time"] = elapsed
            result["page_info"]["final_url"] = page.url
            result["page_info"]["fbcdn_matches_in_html"] = len(image_urls)
            
            await context.close()
            result["success"] = len(image_urls) > 0
            result["steps"].append(f"Done in {elapsed}s. Total images: {len(image_urls)}")
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
    
    return result


@app.get("/debug/test-video")
async def debug_test_video(prompt: str = "A cat playing piano"):
    """Ultra-detailed debug: Capture everything about video generation."""
    from playwright.async_api import async_playwright
    import asyncio
    import re
    
    result = {
        "logs": [],
        "timestamps": {},
        "page_states": [],
        "extracted_data": {}
    }
    video_urls = []
    
    async with async_playwright() as p:
        try:
            result["logs"].append("Launching browser...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir="./meta_session",
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Load cookies
            storage_json = os.environ.get("STORAGE_STATE")
            if storage_json:
                storage_state = json.loads(storage_json)
                cookies = storage_state.get("cookies", [])
                await context.add_cookies(cookies)
                result["logs"].append(f"Loaded {len(cookies)} cookies")
            else:
                result["logs"].append("WARNING: No STORAGE_STATE env var!")
            
            page = await context.new_page()
            
            # Capture console messages
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # Navigate
            result["timestamps"]["navigate_start"] = "start"
            result["logs"].append("Navigating to meta.ai...")
            await page.goto("https://www.meta.ai", timeout=30000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            result["timestamps"]["navigate_end"] = "done"
            result["url_after_nav"] = page.url
            result["logs"].append(f"Navigated to: {page.url}")
            
            # Check if logged in - with error handling
            try:
                page_text = await page.evaluate("() => document.body.innerText.slice(0, 500)")
                result["page_text_after_nav"] = page_text
                result["is_logged_in"] = "log in" not in page_text.lower() and "sign up" not in page_text.lower()
                result["logs"].append(f"Logged in: {result['is_logged_in']}")
            except Exception as eval_err:
                result["logs"].append(f"Warning: Could not evaluate page text: {str(eval_err)}")
                result["is_logged_in"] = False
            
            # Find and check textarea - with retry
            textarea = None
            for attempt in range(3):
                try:
                    textarea = await page.query_selector('textarea[data-testid="composer-input"]')
                    if textarea:
                        break
                    await asyncio.sleep(1)
                except:
                    pass
            
            result["textarea_found"] = textarea is not None
            if textarea:
                try:
                    placeholder = await textarea.get_attribute('placeholder')
                    result["textarea_placeholder"] = placeholder
                    result["logs"].append(f"Textarea found, placeholder: {placeholder}")
                except:
                    result["logs"].append("Textarea found but could not get placeholder")
            else:
                result["logs"].append("ERROR: Textarea not found!")
                # List all textareas on page
                try:
                    all_textareas = await page.query_selector_all('textarea')
                    result["all_textareas_count"] = len(all_textareas)
                except:
                    pass
            
            # Submit prompt
            video_prompt = f"Generate a video: {prompt}"
            result["logs"].append(f"Submitting: {video_prompt}")
            
            await page.evaluate("""(prompt) => {
                const ta = document.querySelector('textarea[data-testid="composer-input"]');
                if (ta) {
                    ta.value = prompt;
                    ta.dispatchEvent(new Event('input', { bubbles: true }));
                    ta.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }""", video_prompt)
            
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            result["timestamps"]["submitted"] = "done"
            result["logs"].append("Enter pressed")
            
            # Wait and check multiple times
            result["logs"].append("Starting 90s wait for video generation...")
            
            for i in range(30):  # 30 * 3 = 90 seconds
                await asyncio.sleep(3)
                elapsed = (i + 1) * 3
                
                # Log progress every 15 seconds
                if elapsed % 15 == 0:
                    result["logs"].append(f"[{elapsed}s] Checking for videos...")
                
                # Capture URL
                current_url = page.url
                if i == 0:
                    result["url_after_submit"] = current_url
                
                # Get page text to check for status
                try:
                    page_text = await page.evaluate("() => document.body.innerText.slice(0, 800)")
                    
                    # Check for generation status indicators
                    if "generating" in page_text.lower():
                        result["logs"].append(f"[{elapsed}s] Status: Still generating...")
                    if "video" in page_text.lower() and elapsed > 30:
                        result["logs"].append(f"[{elapsed}s] 'video' found in page text")
                except:
                    pass
                
                # Multiple extraction attempts
                
                # 1. Video elements
                videos = await page.query_selector_all('video')
                if videos:
                    result["logs"].append(f"[{elapsed}s] Found {len(videos)} <video> elements")
                    for idx, vid in enumerate(videos):
                        src = await vid.get_attribute('src')
                        poster = await vid.get_attribute('poster')
                        if src and '.mp4' in src and src not in video_urls:
                            video_urls.append(src)
                            result["logs"].append(f"  Video {idx} src: {src[:70]}...")
                        if poster and poster not in video_urls:
                            video_urls.append(poster)
                            result["logs"].append(f"  Video {idx} poster: {poster[:70]}...")
                
                # 2. Video links
                links = await page.query_selector_all('a[href*=".mp4"], a[href*="video"], a[href*="fbcdn"]')
                if links:
                    result["logs"].append(f"[{elapsed}s] Found {len(links)} video-related links")
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and href not in video_urls:
                            video_urls.append(href)
                            result["logs"].append(f"  Link: {href[:70]}...")
                
                # 3. All source attributes
                sources = await page.query_selector_all('source')
                if sources:
                    for src_el in sources:
                        src = await src_el.get_attribute('src')
                        if src and '.mp4' in src and src not in video_urls:
                            video_urls.append(src)
                            result["logs"].append(f"[{elapsed}s] Source: {src[:70]}...")
                
                # 4. HTML extraction every 10 seconds
                if elapsed % 10 == 0 or (not video_urls and elapsed > 45):
                    try:
                        page_html = await page.content()
                        
                        # Check if HTML contains video indicators
                        if '.mp4' in page_html:
                            result["logs"].append(f"[{elapsed}s] .mp4 found in HTML")
                        
                        # Extract with multiple patterns
                        patterns = [
                            (r'https://[^"\s<>]*fbcdn\.net[^"\s<>]*\.mp4[^"\s<>]*', "fbcdn mp4"),
                            (r'https://[^"\s<>]*scontent[^"\s<>]*\.mp4[^"\s<>]*', "scontent mp4"),
                            (r'https://[^"\s<>]*video[^"\s<>]*\.mp4[^"\s<>]*', "video mp4"),
                            (r'https://[^"\s<>]*\.mp4[^"\s<>]*', "any mp4"),
                        ]
                        
                        for pattern, name in patterns:
                            matches = re.findall(pattern, page_html)
                            if matches:
                                result["logs"].append(f"[{elapsed}s] Pattern '{name}': {len(matches)} matches")
                                for url in matches[:3]:  # Limit to first 3
                                    clean_url = url.replace('&amp;', '&')
                                    if clean_url not in video_urls:
                                        video_urls.append(clean_url)
                                        result["logs"].append(f"  URL: {clean_url[:70]}...")
                        
                        # Save HTML snippet around video-related content
                        if 'video' in page_html.lower() and elapsed > 30:
                            # Find video-related sections
                            video_indices = [m.start() for m in re.finditer('video', page_html.lower())]
                            if video_indices:
                                snippets = []
                                for idx in video_indices[:3]:
                                    snippet = page_html[max(0, idx-100):min(len(page_html), idx+200)]
                                    snippets.append(snippet.replace('\n', ' '))
                                result[f"html_video_snippets_{elapsed}s"] = snippets
                    except Exception as html_err:
                        result["logs"].append(f"[{elapsed}s] HTML extraction error: {str(html_err)}")
                
                # Break if we have enough videos
                if len(video_urls) >= 4:
                    result["logs"].append(f"[{elapsed}s] Found 4+ videos, stopping")
                    break
            
            # After waiting, scroll up in the chat to find generated videos
            result["logs"].append("Scrolling up to find videos in history...")
            try:
                # Scroll up multiple times to load chat history
                for scroll in range(5):
                    await page.evaluate("() => window.scrollBy(0, -500)")
                    await asyncio.sleep(1)
                    result["logs"].append(f"Scrolled up {scroll + 1} times")
                    
                    # Check for videos after each scroll
                    videos = await page.query_selector_all('video')
                    if videos:
                        result["logs"].append(f"Found {len(videos)} videos after scrolling")
                        for vid in videos:
                            src = await vid.get_attribute('src')
                            if src and src not in video_urls and '.mp4' in src:
                                video_urls.append(src)
                                result["logs"].append(f"  Video src: {src[:70]}...")
            except Exception as scroll_err:
                result["logs"].append(f"Scroll error: {str(scroll_err)}")
            
            # Final HTML extraction to capture any missed URLs
            result["logs"].append("Doing final HTML extraction...")
            try:
                page_html = await page.content()
                
                # Look for video URLs with broader patterns
                patterns = [
                    r'https://[^"\s<>]*fbcdn\.net[^"\s<>]*\.mp4[^"\s<>]*',
                    r'https://[^"\s<>]*scontent[^"\s<>]*\.mp4[^"\s<>]*',
                    r'https://[^"\s<>]*video[^"\s<>]*\.mp4[^"\s<>]*',
                    r'https://[^"\s<>]*\.mp4[^"\s<>]*',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_html)
                    if matches:
                        result["logs"].append(f"Final scan - Pattern found {len(matches)} matches")
                        for url in matches[:5]:
                            clean_url = url.replace('&amp;', '&')
                            if clean_url not in video_urls and '.mp4' in clean_url:
                                video_urls.append(clean_url)
                                result["logs"].append(f"  URL: {clean_url[:70]}...")
            except Exception as final_err:
                result["logs"].append(f"Final extraction error: {str(final_err)}")
            
            # Final summary
            result["timestamps"]["finished"] = "done"
            result["total_video_urls"] = len(video_urls)
            result["video_urls"] = video_urls[:6]
            result["console_logs"] = console_logs[-20:]  # Last 20 console messages
            
            # Try to get final page state
            try:
                final_text = await page.evaluate("() => document.body.innerText.slice(0, 1000)")
                result["final_page_text"] = final_text
            except:
                pass
            
            await context.close()
            result["success"] = True
            result["logs"].append(f"Debug complete. Found {len(video_urls)} videos.")
            
        except Exception as e:
            result["error"] = str(e)
            result["error_type"] = type(e).__name__
            result["success"] = False
            result["logs"].append(f"ERROR: {str(e)}")
    
    return result


@app.get("/debug/test-generate")
async def debug_test_generate():
    """Debug: Actually try to generate and capture full flow."""
    from playwright.async_api import async_playwright
    import asyncio
    
    result = {"logs": []}
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="./meta_session",
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Load cookies
            storage_json = os.environ.get("STORAGE_STATE")
            if storage_json:
                storage_state = json.loads(storage_json)
                await context.add_cookies(storage_state.get("cookies", []))
            
            page = await context.new_page()
            
            # Navigate
            result["logs"].append("Navigating...")
            await page.goto("https://www.meta.ai", timeout=30000)
            await asyncio.sleep(2)
            
            result["url_after_nav"] = page.url
            result["logs"].append(f"Navigated to: {page.url}")
            
            # Check textarea
            textarea = await page.query_selector('textarea[data-testid="composer-input"]')
            result["textarea_exists"] = textarea is not None
            
            if textarea:
                result["logs"].append("Textarea found, trying to submit...")
                
                # Try multiple methods to submit
                prompt = "A red apple"
                
                # Method 1: Direct evaluation
                await page.evaluate("""(prompt) => {
                    const ta = document.querySelector('textarea[data-testid="composer-input"]');
                    if (ta) {
                        ta.value = prompt;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                        return 'set';
                    }
                    return 'not found';
                }""", prompt)
                
                await asyncio.sleep(1)
                
                # Press Enter
                await page.keyboard.press("Enter")
                result["logs"].append("Enter pressed")
                
                # Wait for generation
                await asyncio.sleep(15)
                result["logs"].append("Waited 15s")
                
                result["url_after_submit"] = page.url
                
                # Look for images
                images = await page.query_selector_all('img[src*="fbcdn.net"]')
                result["fbcdn_images_found"] = len(images)
                result["logs"].append(f"Found {len(images)} fbcdn images")
                
                # Get all image srcs
                image_urls = []
                for i, img in enumerate(images[:5]):
                    src = await img.get_attribute('src')
                    image_urls.append(src[:80] if src else None)
                result["image_urls_preview"] = image_urls
                
                # Get page HTML around images
                page_html = await page.content()
                if 'fbcdn.net' in page_html:
                    # Extract fbcdn URLs
                    import re
                    fbcdn_urls = re.findall(r'https://[^"\s]*fbcdn\.net[^"\s]*', page_html)
                    result["fbcdn_urls_in_html"] = fbcdn_urls[:5]
            else:
                result["logs"].append("Textarea NOT found!")
                # Capture page content for debugging
                page_text = await page.evaluate("() => document.body.innerText.slice(0, 500)")
                result["page_text_snippet"] = page_text
            
            await context.close()
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
    
    return result


@app.get("/debug/meta-page")
async def debug_meta_page():
    """Debug: Load meta.ai and capture page HTML to see what's happening."""
    from playwright.async_api import async_playwright
    import asyncio
    
    result = {"logs": []}
    
    # First check what cookies we have in env
    storage_json = os.environ.get("STORAGE_STATE")
    if storage_json:
        try:
            storage_state = json.loads(storage_json)
            cookies = storage_state.get("cookies", [])
            result["env_cookies_count"] = len(cookies)
            result["cookie_names"] = [c.get("name") for c in cookies]
            result["cookie_domains"] = list(set([c.get("domain") for c in cookies if c.get("domain")]))
        except Exception as e:
            result["env_cookie_error"] = str(e)
    else:
        result["env_cookies_count"] = 0
        result["storage_state_missing"] = True
    
    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="./meta_session",
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            
            # Load cookies
            if storage_json:
                try:
                    storage_state = json.loads(storage_json)
                    cookies = storage_state.get("cookies", [])
                    await context.add_cookies(cookies)
                    result["cookies_added"] = len(cookies)
                except Exception as e:
                    result["cookie_add_error"] = str(e)
            
            # Get cookies that are actually in context
            cookies_after = await context.cookies()
            result["cookies_in_context"] = len(cookies_after)
            result["cookie_names_in_context"] = [c.get("name") for c in cookies_after]
            
            page = await context.new_page()
            
            # Navigate
            result["logs"].append("Navigating to meta.ai...")
            await page.goto("https://www.meta.ai", timeout=30000)
            await asyncio.sleep(2)
            
            result["url"] = page.url
            result["logs"].append(f"Page loaded: {page.url}")
            
            # Get page content
            page_text = await page.evaluate("() => document.body.innerText.slice(0, 1000)")
            result["page_text"] = page_text
            result["logs"].append(f"Page text preview: {page_text[:200]}")
            
            # Check for login prompt
            if "log in" in page_text.lower() or "sign in" in page_text.lower():
                result["login_required"] = True
            
            # Check for textarea
            textarea = await page.query_selector('textarea[data-testid="composer-input"]')
            result["textarea_found"] = textarea is not None
            
            await context.close()
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
    
    return result


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables."""
    meta_cookies = os.environ.get("META_COOKIES", "NOT SET")
    storage_state = os.environ.get("STORAGE_STATE", "NOT SET")
    return {
        "meta_cookies_set": meta_cookies != "NOT SET",
        "meta_cookies_length": len(meta_cookies) if meta_cookies != "NOT SET" else 0,
        "storage_state_set": storage_state != "NOT SET",
        "storage_state_length": len(storage_state) if storage_state != "NOT SET" else 0,
        "active_cookie_source": "STORAGE_STATE" if storage_state != "NOT SET" else ("META_COOKIES" if meta_cookies != "NOT SET" else "NONE")
    }


@app.get("/download-video")
async def download_video_proxy(url: str = Query(..., description="Video URL to download")):
    """Download video from URL using cookies and return as stream."""
    import aiohttp
    import asyncio
    
    # Get cookies from environment
    storage_json = os.environ.get("STORAGE_STATE")
    cookies = {}
    if storage_json:
        try:
            storage_state = json.loads(storage_json)
            for cookie in storage_state.get("cookies", []):
                if cookie.get("name") and cookie.get("value"):
                    cookies[cookie["name"]] = cookie["value"]
        except:
            pass
    
    try:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    return {"error": f"Failed to download: HTTP {response.status}"}
                
                content = await response.read()
                
                from fastapi.responses import StreamingResponse
                import io
                
                return StreamingResponse(
                    io.BytesIO(content),
                    media_type="video/mp4",
                    headers={
                        "Content-Disposition": f'attachment; filename="video_{hash(url) % 10000}.mp4"'
                    }
                )
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint - supports both GET and HEAD."""
    return {"status": "ok", "service": "Meta AI Generation API"}

