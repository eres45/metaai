from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import FileResponse
from complete_service import get_service, MetaGenerationService
import asyncio
import os

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
