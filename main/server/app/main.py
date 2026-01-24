from requests import Session
import os
from pathlib import Path
from .utils import StoreJob
from .utils import get_file_path_from_db, heartbeat_handler
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
from requests_toolbelt import MultipartEncoder
from fastapi import APIRouter
from sqlalchemy import distinct, func

from . import app
from .db import SessionLocal
from .models import Jobs
from .logger import get_logger

logger = get_logger(__name__)

@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}

@app.get("/status")
async def status():
    logger.info("Status requested")
    return {'status': 'running'}

@app.get("/")
async def root():
    logger.info("Root requested")
    return {"message": "Hello World"}

@app.get('/request-new-job')
async def request_new_job():
    logger.info("New job requested by worker")
    job = StoreJob.get_next_job()  # returns dict with ulid, filename, etc.
    if job:
        logger.info(f"Job {job['ulid']} assigned to worker")
        job['job_available'] = True
        return job
    
    else:
        logger.info("No new jobs available")
        return {'job_available': False}

@app.get('/request-mp3/{ulid}')
async def request_mp3(ulid):
    logger.info(f"MP3 file for job {ulid} requested")
    file_path = get_file_path_from_db(ulid)
    if not file_path or not os.path.exists(file_path):
        logger.error(f"MP3 file for job {ulid} not found")
        raise HTTPException(status_code=404, detail="MP3 not found")
    logger.info(f"MP3 file for job {ulid} returned")
    return FileResponse(file_path, media_type="audio/mpeg", filename=f"{ulid}.mp3")

@app.post("/new-job")
async def new_job(
    priority_level: str = Form("low"),
    whisper_model: str = Form("medium"),
    ulid: str = Form(None),  # user can provide ULID if they want
    file: UploadFile = File(...)
    ):
    """
    Endpoint to create a new job

    required parameters (multipart/form-data):
    - priority_level (optional, defaults to "low")
    - file (the audio file to be transcribed)
    """
    logger.info(f"New job creation request received for file: {file.filename}")
    job = StoreJob(
        priority_level=priority_level,
        whisper_model=whisper_model,
        filename=file.filename, 
        file=file,
        ulid=ulid
        )
    
    # Store the job and return status
    storeage_status = job.store()
    if storeage_status != "success":
        logger.error(f"Failed to store job for file: {file.filename}")
        return {
            "error": "Failed to store job",
            "status": storeage_status
        }
    else:
        logger.info(f"Job {job.ulid} created successfully for file: {file.filename}")
        return {
            "job_ulid": job.ulid,
            "status": 'deployed'
            }

@app.get("/heartbeat/{ulid}")
async def heartbeat(ulid):
    logger.debug(f"Heartbeat received for job {ulid}")
    heartbeat_status = heartbeat_handler(ulid)
    if heartbeat_status != 'good':
        logger.warning(f"Heartbeat status for job {ulid} is not good: {heartbeat_status}")
        return {'message': 'possible error. Please inspect'}
    
    return {'message': 'acknowledged'}

@app.get("/check-transcript-status/{ulid}")
async def check_transcript_status(ulid: str):
    """
    Checks if a transcript has already been submitted for a given job ULID.
    """
    logger.info(f"Checking transcript status for job {ulid}")
    db = SessionLocal()
    try:
        job = db.query(Jobs).filter(Jobs.ulid == ulid).first()
        if job and job.transcript_path:
            logger.info(f"Transcript found for job {ulid}")
            return {"has_transcript": True}
        logger.info(f"No transcript found for job {ulid}")
        return {"has_transcript": False}
    finally:
        db.close()

@app.post("/return-job")
async def return_job(
    ulid: str = Form(...),
    transcript: str = Form(...)
):
    """
    Endpoint for the worker to return the transcription result.
    The transcript is saved to a .txt file in the same directory as the audio file.
    The database is updated with the path to the transcript file.
    """
    logger.info(f"Job {ulid} returned by worker")
    db = SessionLocal()
    try:
        job = db.query(Jobs).filter(Jobs.ulid == ulid).first()
        if not job:
            logger.error(f"Job {ulid} not found in database")
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
        logger.info(f"Transcript for job {ulid} saved to {transcript_path}")

        # Update the database
        job.transcript_path = str(transcript_path)
        job.status = "completed"
        db.commit()
        logger.info(f"Job {ulid} status updated to completed")

        return {"status": "success", "ulid": ulid, "message": "Transcription received and saved."}
    finally:
        db.close()

@app.get('/report-job-status/{ulid}')
async def report_job_status(ulid):
    '''Report job status to whoever requests it'''
    logger.info(f"Job status requested for {ulid}")
    session = SessionLocal()
    
    try:
        query = session.query(Jobs)
        query = query.filter(Jobs.ulid == ulid)
        job = query.first()
        
        if not job:
            logger.warning(f"Job {ulid} not found for status report")
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_status = job.status
        job_creation_time = job.created_at
        job_update = job.updated_at
        
        data_packet = {
            'status': job_status,
            'created_at': job_creation_time,
            'updated_at': job_update
        }
        
        return data_packet
    
    except Exception as e:
        logger.error(f"Error reporting job status for {ulid}: {e}")
        data_packet = {
            'status': 'invalid_ulid'
        }
        return data_packet
    
    finally:
        session.close()

@app.get('/retrieve-job/{ulid}')
async def retrieve_job(ulid):
    logger.info(f"Retrieval requested for job {ulid}")
    session = SessionLocal()
    try:
        job = session.query(Jobs).filter(Jobs.ulid == ulid).first()

        if not job:
            logger.warning(f"Job {ulid} not found for retrieval")
            raise HTTPException(status_code=404, detail="Job not found")

        # Allow retrieval for completed or already retrieved jobs
        if job.status not in ['completed', 'retrieved']:
            logger.warning(f"Job {ulid} not completed. Current status: {job.status}")
            raise HTTPException(status_code=400, detail=f"Job not completed. Current status: {job.status}")

        if not job.transcript_path or not Path(job.transcript_path).exists():
            logger.error(f"Transcript for job {ulid} not found at {job.transcript_path}")
            raise HTTPException(status_code=404, detail="Transcript file not found")
        
        transcript_path = job.transcript_path
        file_name = os.path.basename(transcript_path)

        # Update status to 'retrieved' if it's not already
        if job.status == 'completed':
            job.status = 'retrieved'
            session.commit()
            logger.info(f"Job {ulid} status updated to retrieved")

            # Delete the original audio file only on the first retrieval
            audio_path = Path(job.file_path)
            if audio_path.exists():
                os.remove(audio_path)
                logger.info(f"Original audio file for job {ulid} deleted")

        return FileResponse(path=transcript_path, media_type='text/plain', filename=file_name)

    except Exception as e:
        session.rollback()
        logger.error(f"Error in retrieve_job for ulid {ulid}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        session.close()

@app.get('/report-transcription-stats')
def report_transcription_stats():
    logger.info("Transcription stats report requested")
    session = SessionLocal()
    data_packet = {}

    try:
        distinct_statuses = session.query(distinct(Jobs.status)).all()

        # This returns a list of tuples, so you might want to flatten it
        distinct_statuses = [status[0] for status in distinct_statuses] # list of status
        data_packet['distinct_statuses'] = distinct_statuses

        for status in distinct_statuses:
            query = session.query(func.count(Jobs.id))
            query = query.filter(Jobs.status == status)
            count = query.scalar()

            data_packet[f'count_status_{status}'] = count
        
        query = session.query(func.count(Jobs.id))
        total_jobs_count = query.scalar()
        data_packet['total_job_count'] = total_jobs_count

        logger.info("Transcription stats report generated")
        return data_packet

    except Exception as e:
        logger.error(f"Error generating transcription stats report: {e}")
        raise HTTPException(status_code=404, detail=str(e))


    finally:
        session.close()

@app.get('/transcription-failure/{ulid}')
def transcription_failure(ulid):
    logger.warning(f"Transcription failure reported for job {ulid}")
    session = SessionLocal()

    try:
        job = session.query(Jobs).filter(Jobs.ulid == ulid).first()
        if not job:
            logger.error(f"Job {ulid} not found on transcription failure report")
            raise HTTPException(status_code=404, detail="Job not found")

        # reset the status of the job
        job.status = 'failed'
        session.commit()
        logger.info(f"Job {ulid} status updated to failed")
    except Exception as e:
        session.rollback()
        logger.error(f"Error in transcription-failure api for ulid {ulid}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        session.close()
