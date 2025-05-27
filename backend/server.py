from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime
import io
from rembg import remove
from PIL import Image

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection (optional - only for status endpoints)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'background_removal_db')

try:
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    MONGODB_AVAILABLE = True
    logger.info(f"Connected to MongoDB at {mongo_url}")
except Exception as e:
    logger.warning(f"MongoDB connection failed: {e}. Status endpoints will be disabled.")
    MONGODB_AVAILABLE = False
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(title="Background Removal API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ImageProcessingResult(BaseModel):
    message: str
    processing_time: float
    original_size: int
    processed_size: int

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Background Removal API Ready"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    """
    Remove background from uploaded image using AI model
    Returns PNG image with transparent background
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        
        # Check file size (limit to 20MB)
        MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds 20MB limit")
        
        # Store original size for metrics
        original_size = len(file_content)
        
        # Process image with rembg
        import time
        start_time = time.time()
        
        # Remove background using rembg
        output_data = remove(file_content)
        
        processing_time = time.time() - start_time
        processed_size = len(output_data)
        
        # Log processing metrics
        logger.info(f"Image processed: {original_size} -> {processed_size} bytes in {processing_time:.2f}s")
        
        # Return processed image as PNG
        return Response(
            content=output_data,
            media_type="image/png",
            headers={
                "Content-Disposition": "attachment; filename=background_removed.png",
                "X-Processing-Time": str(processing_time),
                "X-Original-Size": str(original_size),
                "X-Processed-Size": str(processed_size)
            }
        )
        
    except Exception as e:
        logger.error(f"Background removal failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@api_router.post("/remove-background-base64")
async def remove_background_base64(file: UploadFile = File(...)):
    """
    Remove background and return base64 encoded result for frontend display
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
        
        # Check file size (limit to 20MB)
        MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds 20MB limit")
        
        # Store original size for metrics
        original_size = len(file_content)
        
        # Process image with rembg
        import time
        import base64
        start_time = time.time()
        
        # Remove background using rembg
        output_data = remove(file_content)
        
        processing_time = time.time() - start_time
        processed_size = len(output_data)
        
        # Convert to base64 for frontend display
        base64_result = base64.b64encode(output_data).decode('utf-8')
        
        # Also convert original for comparison
        base64_original = base64.b64encode(file_content).decode('utf-8')
        
        # Log processing metrics
        logger.info(f"Image processed: {original_size} -> {processed_size} bytes in {processing_time:.2f}s")
        
        return {
            "success": True,
            "original_image": f"data:{file.content_type};base64,{base64_original}",
            "processed_image": f"data:image/png;base64,{base64_result}",
            "processing_time": processing_time,
            "original_size": original_size,
            "processed_size": processed_size,
            "message": "Background removed successfully"
        }
        
    except Exception as e:
        logger.error(f"Background removal failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging already configured above

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()