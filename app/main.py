from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
import time
import asyncio
from app.services.nanobanana import NanoBananaAPI

app = FastAPI(title="NanoBanana Plan Scaler")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_details = traceback.format_exc()
    print(f"CRITICAL: Unhandled exception: {error_details}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}", "trace": str(exc)},
    )

# Setup directories
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# NanoBanana Client
nanobanana = NanoBananaAPI()

DEFAULT_PROMPT = "I want you to clean this plan and also dimension it and label it and make sure the wall thickness are up to standard. Edit the plan where necessary to make sure it meets the standard"

# --- Background Task for File Cleanup ---
def cleanup_old_files(directory: str, max_age_seconds: int = 3600):
    """Deletes files older than max_age_seconds to prevent disk fill-up."""
    try:
        now = time.time()
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # Skip .gitkeep or directories
            if not os.path.isfile(file_path) or filename.startswith('.'):
                continue
                
            if os.stat(file_path).st_mtime < now - max_age_seconds:
                os.remove(file_path)
                print(f"Cleanup: Deleted old file {filename}")
    except Exception as e:
        print(f"Error during file cleanup: {e}")

@app.post("/api/process")
async def process_plan(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 0. Trigger cleanup occasionally
    background_tasks.add_task(cleanup_old_files, UPLOAD_DIR)

    # Sanitize content_type
    content_type = file.content_type or "application/octet-stream"

    if not content_type.startswith("image/") and not content_type == "application/octet-stream":
        # We might be lenient here or check filename extension as fallback
        pass 
    
    # Strict check if we want, but let's be safe against None
    if file.content_type and not file.content_type.startswith("image/"):
         raise HTTPException(status_code=400, detail=f"File must be an image, got {file.content_type}")

    # 1. Save file locally
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"ERROR: Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file on server")
    
    # 2. Construct URL
    # FIX: Render terminates SSL, so request.base_url might say 'http'. 
    # We force 'https' if the header 'x-forwarded-proto' is 'https', or just assume https for production.
    # A safe generic way for Render/Proxies:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    base_url = str(request.base_url).rstrip("/")
    
    if forwarded_proto == "https" and base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://", 1)
    
    image_url = f"{base_url}/static/uploads/{filename}"
    
    print(f"DEBUG: Process Request. Image URL generated: {image_url}")
    
    try:
        # 3. Call NanoBanana API (Async)
        task_id = await nanobanana.generate_image(
            prompt=DEFAULT_PROMPT,
            imageUrls=[image_url],
            type="TEXTTOIAMGE" 
        )
        
        return {"taskId": task_id, "status": "processing", "originalImageUrl": image_url}
        
    except Exception as e:
        print(f"CRITICAL ERROR calling NanoBanana: {e}")
        # Return 500 but with detail so we can see it in client response
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    try:
        status = await nanobanana.get_task_status(task_id)
        return status
    except Exception as e:
        print(f"Error checking status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return JSONResponse(content={"message": "Visit /static/index.html to use the app"})
