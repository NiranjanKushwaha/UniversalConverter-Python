from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from uuid import uuid4
import os
import asyncio
import aiofiles
from typing import List, Dict
from conversion_service import ConversionService

app = FastAPI(title="Universal File Converter API", version="1.0.0")

# Enable CORS for all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize conversion service
conversion_service = ConversionService()

# In-memory job store (replace with persistent storage in production)
jobs = {}

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

@app.post("/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sourceFormat: str = Form(...),
    destinationFormat: str = Form(...)
):
    try:
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
            raise HTTPException(
                status_code=400, 
                detail=f"Conversion from {sourceFormat} to {destinationFormat} is not supported"
            )
        
        # Generate job ID and file paths
        job_id = str(uuid4())
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        upload_filename = f"{job_id}_input{file_extension}"
        upload_path = os.path.join(UPLOAD_DIR, upload_filename)
        
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
        
        # Save uploaded file
        async with aiofiles.open(upload_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Initialize job status
        jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "upload_path": upload_path,
            "converted_path": output_path,
            "error": None,
            "source_format": source_format,
            "destination_format": destination_format,
            "original_filename": file.filename
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
        
        return {"jobId": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/status/{jobId}")
def get_status(jobId: str):
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    resp = {
        "status": job["status"],
        "progress": job["progress"],
        "downloadUrl": f"/download/{jobId}" if job["status"] == "completed" else None,
        "error": job["error"]
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

@app.delete("/jobs/{jobId}")
def delete_job(jobId: str):
    """Delete a job and clean up associated files"""
    job = jobs.get(jobId)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up files
    try:
        if job.get("upload_path") and os.path.exists(job["upload_path"]):
            os.remove(job["upload_path"])
        if job.get("converted_path") and os.path.exists(job["converted_path"]):
            os.remove(job["converted_path"])
    except Exception as e:
        # Log error but don't fail the deletion
        print(f"Error cleaning up files for job {jobId}: {e}")
    
    # Remove job from memory
    del jobs[jobId]
    
    return {"message": f"Job {jobId} deleted successfully"}

@app.get("/jobs")
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
    return {"jobs": job_list}
