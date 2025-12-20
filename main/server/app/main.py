from . import app
import os
from pathlib import Path
import json
from .utils import StoreJob
from .utils import get_file_path_from_db
from .utils import heartbeat_handler
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from requests_toolbelt import MultipartEncoder
from fastapi import APIRouter

from .db import SessionLocal
from .models import Jobs

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

@app.get("/heartbeat/{ulid}")
async def heartbeat(ulid):
    heartbeat_status = heartbeat_handler(ulid)
    if heartbeat_status != 'good':
        return {'message': 'possible error. Please inspect'}
    
    return {'message': 'acknowledged'}

@app.get("/check-transcript-status/{ulid}")
async def check_transcript_status(ulid: str):
    """
    Checks if a transcript has already been submitted for a given job ULID.
    """
    db = SessionLocal()
    try:
        job = db.query(Jobs).filter(Jobs.ulid == ulid).first()
        if job and job.transcript_path:
            return {"has_transcript": True}
        return {"has_transcript": False}
    finally:
        db.close()

@app.post("/return-job")
async def return_job(
    ulid: str = Form(...),
    transcript: str = Form(...)
):
    """
    Endpoint for the worker to return the transcri][un7hn7,nm.mp0
    ption result.
    The transcript is saved to a .txt file in the same directory as the audio file.
    The database is updated with the path to the transcript file.
    """
    db = SessionLocal()
    try:
        job = db.query(Jobs).filter(Jobs.ulid == ulid).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get the directory of the audio file
        audio_file_path = Path(job.file_path)
        transcript_dir = audio_file_path.parent

        # Create the transcript file name and path
        transcript_filename = f"{Path(job.file_name).stem}.txt"
        transcript_path = transcript_dir / transcript_filename

        # Save the transcript to the file
        with open(transcript_path, "w") as f:
            f.write(transcript)

        # Update the database
        job.transcript_path = str(transcript_path)
        job.status = "completed"
        db.commit()

        return {"status": "success", "ulid": ulid, "message": "Transcription received and saved."}
    finally:
        db.close()
