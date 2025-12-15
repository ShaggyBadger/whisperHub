from app import app
from .utils import StoreJob
from fastapi import UploadFile, File, Form

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Hello World"}

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
