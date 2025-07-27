from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from uuid import uuid4
import os
import asyncio
import aiofiles
import shutil
import uuid
import hashlib
from typing import List, Dict
from conversion_service import ConversionService
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal File Converter API", version="1.0.0")

# Enable CORS for all origins (adjust as needed)
# WARNING: For production, restrict allow_origins to specific domains to prevent security risks.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Consider changing to specific origins in production, e.g., ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize conversion service
conversion_service = ConversionService()

# In-memory job store (replace with persistent storage in production)
# For production, consider using a database (e.g., PostgreSQL, Redis) for persistent job storage
# and better scalability.
jobs = {}

# File hash mapping to avoid storing duplicate files
file_hash_mapping = {}  # hash -> {filename, upload_path}

# Security configurations
API_KEY = os.getenv("API_KEY") # Load API key from environment variable
MAX_FILE_SIZE_MB = 100 # Maximum file size allowed for upload in MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Dependency for API Key authentication
async def get_api_key(api_key: str = Depends(lambda x: x.headers.get("X-API-Key"))):
    if API_KEY is None:
        logger.warning("API_KEY environment variable is not set. API key authentication is disabled.")
        return True # Allow access if API_KEY is not set (for development convenience)
    
    if api_key is None or api_key != API_KEY:
        logger.warning(f"Unauthorized access attempt with API Key: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return True

# Example supported formats (expand as needed)
supported_formats = [
      {
        "source": "PDF",
        "destination": ["DOCX", "DOC", "XLSX", "XLS", "HTML", "JPG", "PNG", "TIFF", "GIF", "TXT", "PPT", "PPTX", "CSV", "XML", "EPUB", "MOBI"]
      },
      {
        "source": "DOCX",
        "destination": ["PDF", "HTML", "TXT", "RTF", "ODT", "XML", "EPUB", "MOBI", "JPG", "PNG"]
      },
      {
        "source": "DOC",
        "destination": ["PDF", "HTML", "TXT", "RTF", "ODT", "XML", "EPUB", "MOBI", "JPG", "PNG"]
      },
      {
        "source": "XLSX",
        "destination": ["CSV", "PDF", "HTML", "XML", "ODS", "TXT", "JSON"]
      },
      {
        "source": "XLS",
        "destination": ["CSV", "PDF", "HTML", "XML", "ODS", "TXT", "JSON"]
      },
      {
        "source": "JPEG/JPG",
        "destination": ["PDF", "PNG", "BMP", "GIF", "TIFF", "WEBP", "SVG", "ICO", "DOCX", "DOC", "PPTX", "TXT"]
      },
      {
        "source": "PNG",
        "destination": ["PDF", "JPG", "BMP", "GIF", "TIFF", "WEBP", "SVG", "ICO", "DOCX", "DOC", "XLSX", "PPTX", "TXT"]
      },
      {
        "source": "BMP",
        "destination": ["PDF", "JPG", "PNG", "GIF", "TIFF", "WEBP", "SVG", "ICO", "DOCX", "DOC", "TXT"]
      },
      {
        "source": "GIF",
        "destination": ["PDF", "JPG", "PNG", "BMP", "TIFF", "WEBP", "SVG", "ICO", "DOCX", "DOC"]
      },
      {
        "source": "TIFF",
        "destination": ["PDF", "JPG", "PNG", "BMP", "GIF", "WEBP", "SVG", "ICO", "DOCX", "DOC", "TXT"]
      },
      {
        "source": "TXT",
        "destination": ["DOCX", "DOC", "PDF", "HTML", "RTF", "ODT", "EPUB", "MOBI", "CSV", "XML", "JSON", "MP3"]
      },
      {
        "source": "XML",
        "destination": ["DOCX", "PDF", "HTML", "TXT", "XLSX", "XLS", "CSV", "JSON"]
      },
      {
        "source": "HTML",
        "destination": ["PDF", "DOCX", "DOC", "TXT", "EPUB", "MOBI", "JPG", "PNG"]
      },
      {
        "source": "CSV",
        "destination": ["XLSX", "XLS", "PDF", "HTML", "XML", "JSON", "TXT"]
      },
      {
        "source": "PPTX",
        "destination": ["PDF", "JPG", "PNG", "PPT", "HTML", "ODP"]
      },
      {
        "source": "PPT",
        "destination": ["PDF", "JPG", "PNG", "PPTX", "HTML", "ODP"]
      },
      {
        "source": "RTF",
        "destination": ["DOCX", "DOC", "PDF", "HTML", "TXT", "ODT"]
      },
      {
        "source": "ODT",
        "destination": ["DOCX", "DOC", "PDF", "HTML", "TXT", "RTF", "EPUB", "MOBI"]
      },
      {
        "source": "ODS",
        "destination": ["XLSX", "XLS", "CSV", "PDF", "HTML", "XML", "JSON"]
      },
      {
        "source": "ODP",
        "destination": ["PPTX", "PPT", "PDF", "JPG", "PNG", "HTML"]
      },
      {
        "source": "EPUB",
        "destination": ["PDF", "MOBI", "AZW3", "TXT", "HTML", "DOCX", "DOC"]
      },
      {
        "source": "MOBI",
        "destination": ["PDF", "EPUB", "AZW3", "TXT", "HTML", "DOCX", "DOC"]
      },
      {
        "source": "AZW3",
        "destination": ["PDF", "EPUB", "MOBI", "TXT", "HTML", "DOCX", "DOC"]
      },
      {
        "source": "JSON",
        "destination": ["XML", "CSV", "TXT", "HTML", "XLSX", "XLS"]
      },
      {
        "source": "WEBP",
        "destination": ["JPG", "PNG", "BMP", "GIF", "TIFF", "PDF", "SVG", "ICO"]
      },
      {
        "source": "SVG",
        "destination": ["PNG", "JPG", "PDF", "WEBP", "BMP", "GIF", "TIFF"]
      },
      {
        "source": "MP3",
        "destination": ["WAV", "AAC", "FLAC", "OGG", "M4A"]
      },
      {
        "source": "WAV",
        "destination": ["MP3", "AAC", "FLAC", "OGG", "M4A"]
      },
      {
        "source": "MP4",
        "destination": ["AVI", "MOV", "WMV", "FLV", "MKV", "WEBM", "MP3", "WAV", "GIF"]
      },
      {
        "source": "AVI",
        "destination": ["MP4", "MOV", "WMV", "FLV", "MKV", "WEBM", "MP3", "WAV", "GIF"]
      },
      {
        "source": "MOV",
        "destination": ["MP4", "AVI", "WMV", "FLV", "MKV", "WEBM", "MP3", "WAV", "GIF"]
      }
    ]

UPLOAD_DIR = "uploads"
CONVERTED_DIR = "converted"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)

async def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()

async def get_or_create_file_path(content: bytes, original_filename: str) -> tuple[str, str]:
    """
    Check if file already exists by hash, return existing path or create new one.
    Returns: (upload_path, file_hash)
    """
    file_hash = await calculate_file_hash(content)
    
    # Check if we already have this file
    if file_hash in file_hash_mapping:
        existing_info = file_hash_mapping[file_hash]
        return existing_info["upload_path"], file_hash
    
    # Create new file entry
    file_extension = os.path.splitext(original_filename)[1] if original_filename else ""
    upload_filename = f"{file_hash}{file_extension}"
    upload_path = os.path.join(UPLOAD_DIR, upload_filename)
    
    # Save the file
    async with aiofiles.open(upload_path, 'wb') as f:
        await f.write(content)
    
    # Store mapping
    file_hash_mapping[file_hash] = {
        "filename": upload_filename,
        "upload_path": upload_path
    }
    
    return upload_path, file_hash

async def perform_conversion(job_id: str, upload_path: str, output_path: str, source_format: str, destination_format: str):
    """Background task to perform file conversion"""
    try:
        await conversion_service.convert_file(
            input_path=upload_path,
            output_path=output_path,
            source_format=source_format,
            destination_format=destination_format,
            job_id=job_id,
            jobs=jobs
        )
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

async def is_file_in_use(file_hash: str, current_job_id: str) -> bool:
    """Check if a file is still being used by other jobs"""
    for job_id, job in jobs.items():
        if job_id != current_job_id and job.get("file_hash") == file_hash:
            return True
    return False

async def cleanup_unused_files():
    """Remove files that are no longer referenced by any jobs"""
    files_to_remove = []
    
    for file_hash, file_info in file_hash_mapping.items():
        is_used = False
        for job in jobs.values():
            if job.get("file_hash") == file_hash:
                is_used = True
                break
        
        if not is_used:
            files_to_remove.append(file_hash)
    
    # Remove unused files
    for file_hash in files_to_remove:
        file_info = file_hash_mapping[file_hash]
        try:
            if os.path.exists(file_info["upload_path"]):
                os.remove(file_info["upload_path"])
            del file_hash_mapping[file_hash]
        except Exception as e:
            print(f"Error removing file {file_info['upload_path']}: {e}")

def cleanup_temp_files(directory: str):
    """Clean up temporary files (files starting with ~$)"""
    try:
        for filename in os.listdir(directory):
            if filename.startswith('~$'):
                temp_file_path = os.path.join(directory, filename)
                if os.path.isfile(temp_file_path):
                    os.remove(temp_file_path)
                    logging.info(f"Cleaned up temporary file: {filename}")
    except Exception as e:
        logging.error(f"Error cleaning up temporary files: {e}")

# Initialize scheduler for periodic cleanup
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(CronTrigger(minute=0))  # Run every hour
async def scheduled_cleanup():
    """Scheduled cleanup of temporary files and unused files"""
    try:
        logging.info("Running scheduled cleanup...")
        await cleanup_unused_files()
        cleanup_temp_files(CONVERTED_DIR)
        cleanup_temp_files(UPLOAD_DIR)
        logging.info("Scheduled cleanup completed")
    except Exception as e:
        logging.error(f"Error in scheduled cleanup: {e}")

# Start the scheduler
scheduler.start()

@app.post("/convert", dependencies=[Depends(get_api_key)])
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sourceFormat: str = Form(...),
    destinationFormat: str = Form(...)
):
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            logger.warning(f"File size exceeds limit: {file.filename} ({len(file_content)} bytes)")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB} MB."
            )
        
        # Sanitize filename to prevent path traversal
        original_filename = os.path.basename(file.filename)
        if ".." in original_filename or "/" in original_filename or "\\" in original_filename:
            logger.warning(f"Attempted path traversal with filename: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Path traversal attempts are not allowed."
            )

        # Validate input formats
        source_format = sourceFormat.upper()
        destination_format = destinationFormat.upper()
        
        # Handle JPEG/JPG format normalization
        if source_format in ["JPEG", "JPG"]:
            source_format = "JPG"
        if destination_format in ["JPEG", "JPG"]:
            destination_format = "JPG"
        
        # Check if conversion is supported
        supported_conversion = False
        for format_info in supported_formats:
            if format_info["source"] == source_format or (format_info["source"] == "JPEG/JPG" and source_format == "JPG"):
                if destination_format in format_info["destination"]:
                    supported_conversion = True
                    break
        
        if not supported_conversion:
            logger.warning(f"Unsupported conversion attempt: {sourceFormat} to {destinationFormat}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Conversion from {sourceFormat} to {destinationFormat} is not supported"
            )
        
        # Generate job ID and file paths
        job_id = str(uuid4())
        
        # Get or create file path based on hash
        upload_path, file_hash = await get_or_create_file_path(file_content, original_filename)
        
        # Log whether file was reused or created new
        if file_hash in file_hash_mapping and any(job.get("file_hash") == file_hash for job in jobs.values()):
            logger.info(f"Reusing existing file with hash {file_hash[:8]}... for job {job_id}")
        else:
            logger.info(f"Created new file with hash {file_hash[:8]}... for job {job_id}")
        
        # Determine output file extension
        output_extension = f".{destination_format.lower()}"
        if destination_format == "JPG":
            output_extension = ".jpg"
        elif destination_format == "DOCX":
            output_extension = ".docx"
        elif destination_format == "XLSX":
            output_extension = ".xlsx"
        elif destination_format == "PPTX":
            output_extension = ".pptx"
        
        output_filename = f"{job_id}_output{output_extension}"
        output_path = os.path.join(CONVERTED_DIR, output_filename)
        
        # Initialize job status
        jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "upload_path": upload_path,
            "converted_path": output_path,
            "error": None,
            "source_format": source_format,
            "destination_format": destination_format,
            "original_filename": original_filename, # Use sanitized filename
            "file_hash": file_hash
        }
        
        # Start background conversion task
        background_tasks.add_task(
            perform_conversion,
            job_id,
            upload_path,
            output_path,
            source_format,
            destination_format
        )
        
        # Clean up any temporary files
        background_tasks.add_task(cleanup_temp_files, CONVERTED_DIR)
        
        logger.info(f"Conversion job {job_id} initiated for {original_filename}.")
        return {"jobId": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file for conversion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred.")

@app.get("/status/{jobId}")
def get_status(jobId: str):
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    resp = {
        "status": job["status"],
        "progress": job["progress"],
        "downloadUrl": f"/download/{jobId}" if job["status"] == "completed" else None,
        "error": job["error"],
        "conversion_method": job.get("conversion_method"),
        "warning": job.get("warning")
    }
    return resp

@app.get("/download/{jobId}")
def download_file(jobId: str):
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File conversion not completed yet.")
    
    if not job["converted_path"] or not os.path.exists(job["converted_path"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Converted file not found.")
    
    # Generate a meaningful filename for download
    original_name = job.get("original_filename", "converted_file")
    name_without_ext = os.path.splitext(original_name)[0]
    destination_format = job.get("destination_format", "").lower()
    
    if destination_format == "jpg":
        download_filename = f"{name_without_ext}.jpg"
    elif destination_format == "docx":
        download_filename = f"{name_without_ext}.docx"
    elif destination_format == "xlsx":
        download_filename = f"{name_without_ext}.xlsx"
    elif destination_format == "pptx":
        download_filename = f"{name_without_ext}.pptx"
    else:
        download_filename = f"{name_without_ext}.{destination_format}"
    
    logger.info(f"Serving download for job {jobId}: {download_filename}")
    return FileResponse(
        job["converted_path"], 
        filename=download_filename,
        media_type='application/octet-stream'
    )

@app.get("/formats")
def get_formats():
    """Get all supported conversion formats"""
    return supported_formats

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Universal File Converter API is running"}

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Universal File Converter API",
        "version": "1.0.0",
        "endpoints": {
            "convert": "POST /convert - Convert a file",
            "status": "GET /status/{jobId} - Check conversion status",
            "download": "GET /download/{jobId} - Download converted file",
            "formats": "GET /formats - Get supported formats",
            "health": "GET /health - Health check"
        }
    }

@app.delete("/jobs/{jobId}", dependencies=[Depends(get_api_key)])
def delete_job(jobId: str):
    """Delete a job and cleanup associated files"""
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    # Remove converted file if it exists
    if job.get("converted_path") and os.path.exists(job["converted_path"]):
        try:
            os.remove(job["converted_path"])
            logger.info(f"Removed converted file for job {jobId}: {job['converted_path']}")
        except Exception as e:
            logger.error(f"Error removing converted file for job {jobId}: {e}")
    
    # Remove job from tracking
    del jobs[jobId]
    
    # Clean up unused files (asynchronously)
    asyncio.create_task(cleanup_unused_files())
    
    logger.info(f"Job {jobId} deleted successfully.")
    return {"message": "Job deleted successfully"}

@app.get("/status/{jobId}")
def get_status(jobId: str):
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    resp = {
        "status": job["status"],
        "progress": job["progress"],
        "downloadUrl": f"/download/{jobId}" if job["status"] == "completed" else None,
        "error": job["error"],
        "conversion_method": job.get("conversion_method"),
        "warning": job.get("warning")
    }
    return resp

@app.get("/download/{jobId}")
def download_file(jobId: str):
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="File conversion not completed yet")
    
    if not job["converted_path"] or not os.path.exists(job["converted_path"]):
        raise HTTPException(status_code=404, detail="Converted file not found")
    
    # Generate a meaningful filename for download
    original_name = job.get("original_filename", "converted_file")
    name_without_ext = os.path.splitext(original_name)[0]
    destination_format = job.get("destination_format", "").lower()
    
    if destination_format == "jpg":
        download_filename = f"{name_without_ext}.jpg"
    elif destination_format == "docx":
        download_filename = f"{name_without_ext}.docx"
    elif destination_format == "xlsx":
        download_filename = f"{name_without_ext}.xlsx"
    elif destination_format == "pptx":
        download_filename = f"{name_without_ext}.pptx"
    else:
        download_filename = f"{name_without_ext}.{destination_format}"
    
    return FileResponse(
        job["converted_path"], 
        filename=download_filename,
        media_type='application/octet-stream'
    )

@app.get("/formats")
def get_formats():
    """Get all supported conversion formats"""
    return supported_formats

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Universal File Converter API is running"}

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Universal File Converter API",
        "version": "1.0.0",
        "endpoints": {
            "convert": "POST /convert - Convert a file",
            "status": "GET /status/{jobId} - Check conversion status",
            "download": "GET /download/{jobId} - Download converted file",
            "formats": "GET /formats - Get supported formats",
            "health": "GET /health - Health check"
        }
    }

@app.delete("/jobs/{jobId}", dependencies=[Depends(get_api_key)])
def delete_job(jobId: str):
    """Delete a job and cleanup associated files"""
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    
    # Remove converted file if it exists
    if job.get("converted_path") and os.path.exists(job["converted_path"]):
        try:
            os.remove(job["converted_path"])
            logger.info(f"Removed converted file for job {jobId}: {job['converted_path']}")
        except Exception as e:
            logger.error(f"Error removing converted file for job {jobId}: {e}")
    
    # Remove job from tracking
    del jobs[jobId]
    
    # Clean up unused files (asynchronously)
    asyncio.create_task(cleanup_unused_files())
    
    logger.info(f"Job {jobId} deleted successfully.")
    return {"message": "Job deleted successfully"}

@app.get("/jobs", dependencies=[Depends(get_api_key)])
def list_jobs():
    """List all jobs (for debugging/admin purposes)"""
    job_list = []
    for job_id, job_data in jobs.items():
        job_list.append({
            "jobId": job_id,
            "status": job_data["status"],
            "progress": job_data["progress"],
            "sourceFormat": job_data.get("source_format"),
            "destinationFormat": job_data.get("destination_format"),
            "originalFilename": job_data.get("original_filename"),
            "error": job_data.get("error")
        })
    logger.info("Listed all jobs.")
    return {"jobs": job_list}

@app.get("/cleanup", dependencies=[Depends(get_api_key)])
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Manually trigger cleanup of unused files and temporary files"""
    try:
        background_tasks.add_task(cleanup_unused_files)
        background_tasks.add_task(cleanup_temp_files, CONVERTED_DIR)
        background_tasks.add_task(cleanup_temp_files, UPLOAD_DIR)
        logger.info("Manual cleanup initiated.")
        return {"message": "Cleanup initiated"}
    except Exception as e:
        logger.error(f"Error in cleanup endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during cleanup.")

@app.get("/storage/stats", dependencies=[Depends(get_api_key)])
def get_storage_stats():
    """Get storage statistics"""
    upload_files = len([f for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))])
    converted_files = len([f for f in os.listdir(CONVERTED_DIR) if os.path.isfile(os.path.join(CONVERTED_DIR, f))])
    active_jobs = len(jobs)
    unique_files = len(file_hash_mapping)
    
    logger.info("Retrieved storage statistics.")
    return {
        "upload_files": upload_files,
        "converted_files": converted_files,
        "active_jobs": active_jobs,
        "unique_files": unique_files,
        "file_hash_mapping_size": len(file_hash_mapping)
    }
