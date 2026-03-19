from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import FileResponse
from complete_service import get_service, MetaGenerationService
import asyncio
import os
import json

app = FastAPI(title="Meta AI Generation API")
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Meta AI Generation API"}
