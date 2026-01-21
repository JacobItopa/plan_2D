from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
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

# Setup directories
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# NanoBanana Client
nanobanana = NanoBananaAPI()

DEFAULT_PROMPT = "I want you to clean this plan and also dimension it and label it and make sure the wall thickness are up to standard. Edit the plan where necessary to make sure it meets the standard"

@app.post("/api/process")
async def process_plan(request: Request, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # 1. Save file locally
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. Construct URL
    # IMPORTANT: This URL needs to be accessible by NanoBanana servers.
    # If running locally without tunneling (like ngrok), this might fail if NanoBanana tries to fetch 'localhost'.
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/static/uploads/{filename}"
    
    print(f"Image uploaded to: {image_url}")
    
    try:
        # 3. Call NanoBanana API
        # Only 'IMAGETOIMAGE' or similar type supports input images. 
        # The user example used 'TEXTTOIAMGE' (sic) but passed 'imageUrls'. 
        # We will assume 'IMAGETOIMAGE' is likely intended if we pass an image, 
        # or we stick to the user's example which defaults to 'TEXTTOIAMGE'.
        # Let's try to infer type or stick to user provided logic handling.
        # User code: data['type'] = options.get('type', 'TEXTTOIAMGE')
        # If we provide an image, it usually implies image-to-image. 
        # However, I will check if I should explicitely set it. 
        # For now I will set it to 'IMAGETOIMAGE' as a safe bet for plan editing, 
        # but if the user code had 'TEXTTOIAMGE' as default, I'll allow override or default.
        # Actually, let's look at the prompt: "clean *this* plan". It implies input image.
        
        task_id = nanobanana.generate_image(
            prompt=DEFAULT_PROMPT,
            imageUrls=[image_url],
            type="TEXTTOIAMGE" # Reverting to user-provided type (typo included as it might be required)
        )
        
        return {"taskId": task_id, "status": "processing", "originalImageUrl": image_url}
        
    except Exception as e:
        print(f"Error calling NanoBanana: {e}")
        # If it's a URL reachability issue, we might want to inform the user.
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    try:
        status = nanobanana.get_task_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    # Serve index.html
    return JSONResponse(content={"message": "Visit /static/index.html to use the app"})
