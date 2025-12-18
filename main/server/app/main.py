from app import app
import os
import json
from .utils import StoreJob
from .utils import get_file_path_from_db
from fastapi import UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from requests_toolbelt import MultipartEncoder
from fastapi import APIRouter

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/status")
async def status():
    return {'status': 'running'}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get('/request-new-job')
async def request_new_job():
    job = StoreJob.get_next_job()  # returns dict with ulid, filename, etc.
    if job:
        job['job_available'] = True
        return job
    
    else:
        return {'job_available': False}

@app.get('/request-mp3/{ulid}')
async def request_mp3(ulid):
    file_path = get_file_path_from_db(ulid)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="MP3 not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=f"{ulid}.mp3")

@app.post("/new-job")
async def new_job(
    priority_level: str = Form("low"),
    file: UploadFile = File(...)
):
    """
    Endpoint to create a new job

    required parameters (multipart/form-data):
    - priority_level (optional, defaults to "low")
    - file (the audio file to be transcribed)
    """
    job = StoreJob(
        priority_level=priority_level,
        filename=file.filename, 
        file=file
        )
    
    # Store the job and return status
    storeage_status = job.store()
    if storeage_status != "success":
        return {
            "error": "Failed to store job",
            "status": storeage_status
        }
    else:
        return {
            "job_ulid": job.ulid,
            "status": job.status
            }

