import ulid
from .models import Jobs
from pathlib import Path
from . import db
from sqlalchemy import case
from .logger import get_logger

logger = get_logger(__name__)


# Define the paths for the audio files
AUDIO_FILE_DIR = Path(__file__).parent / "audio_files"

class StoreJob:
    """class to store job info"""
    def __init__(
        self, 
        priority_level = "low",
        filename = "",
        file = None, 
        status = "pending"
        ):

        # generate ULID for the job
        self.ulid = str(ulid.new())
        logger.debug(f"New StoreJob instance created with ULID: {self.ulid}")
        
        # Set status and stuff or default
        self.status = status
        self.filename = filename
        self.priority_level = priority_level
        self.file = file

    def build_mp3_path(self):
        AUDIO_FILE_DIR.mkdir(parents=True, exist_ok=True)
        
        job_path = AUDIO_FILE_DIR / str(self.ulid)
        job_path.mkdir(parents=True, exist_ok=True)
        
        mp3_path = job_path / self.filename
        logger.debug(f"Built MP3 path for ULID {self.ulid}: {mp3_path}")
        return str(mp3_path)
    
    def store(self):
        logger.info(f"Attempting to store job {self.ulid} with filename {self.filename}")
        job_data = {
            "ulid": str(self.ulid),
            "status": self.status,
            "priority_level": self.priority_level,
            "file_name": self.filename,
            "file_path": self.build_mp3_path()
        }

        # return a status code
        status_code = 'processing'
        db_session = db.SessionLocal()
        try:
            job_record = Jobs(**job_data)
            db_session.add(job_record)
            db_session.commit()
            logger.debug(f"Job {self.ulid} recorded in database.")

            # Save the uploaded file to the designated path
            with open(job_data["file_path"], "wb") as out_file:
                content = self.file.file.read()
                out_file.write(content)
            logger.info(f"Audio file for job {self.ulid} saved to {job_data['file_path']}")

            status_code = "success"
        
        except Exception as e:
            logger.error(f"Error storing job {self.ulid}: {e}", exc_info=True)
            db_session.rollback()
            status_code = "error"
        
        finally:
            db_session.close()
            logger.debug(f"Database session closed for job {self.ulid} storage.")
        
        return status_code

    @staticmethod
    def get_next_job():
        logger.info("Worker requesting next job.")
        db_session = db.SessionLocal()
        job = None
        try:
            # update this list with any other relevent statuses
            relevent_status = ['pending', 'failed']

            # try to find high-priority jobs first
            query = db_session.query(Jobs)
            query = query.filter(Jobs.status == 'pending')
            query = query.filter(Jobs.priority_level == 'high')
            query = query.order_by(Jobs.created_at.asc())
            high_priority_job = query.first()

            if high_priority_job:
                job = high_priority_job
                logger.debug(f"Found high priority job: {job.ulid}")

            else:
                # no high priority jobs available. search for low priority jobs
                query = db_session.query(Jobs)
                query = query.filter(Jobs.status.in_(relevent_status))
                query = query.filter(Jobs.priority_level == 'low')
                query = query.order_by(Jobs.created_at.asc())
                low_priority_job = query.first()

                if low_priority_job:
                    job = low_priority_job
                    logger.debug(f"Found low priority job: {job.ulid}")
            
            if job:
                # update job status and return job
                job.status = "transcribing"
                db_session.commit()
                logger.info(f"Job {job.ulid} status updated to 'transcribing' and assigned.")

                job_dict = {
                    'ulid': job.ulid,
                    'priority_level': job.priority_level,
                    'file_name': job.file_name,
                    'file_path': job.file_path,
                    'whisper_model': job.whisper_model
                }

                return job_dict
            else:
                logger.info("No pending or failed jobs found.")
                return None
        except Exception as e:
            logger.error(f"Error requesting new job: {e}", exc_info=True)
            db_session.rollback()
            return None
        
        finally:
            db_session.close()
            logger.debug("Database session closed for get_next_job.")

def get_file_path_from_db(ulid):
    logger.debug(f"Attempting to retrieve file path for ULID: {ulid}")
    db_session = db.SessionLocal()

    try:
        query = db_session.query(Jobs)
        query = query.filter(Jobs.ulid == ulid)
        entry = query.first()

        if entry:
            logger.debug(f"File path for ULID {ulid} found: {entry.file_path}")
            return entry.file_path
        logger.warning(f"No job entry found for ULID: {ulid}")
        return None

    except Exception as e:
        logger.error(f"Error retrieving file path for ULID {ulid}: {e}", exc_info=True)
        db_session.rollback()
        return None
    
    finally:
        db_session.close()
        logger.debug(f"Database session closed for get_file_path_from_db.")

def heartbeat_handler(ulid):
    logger.debug(f"Handling heartbeat for ULID: {ulid}")
    session = db.SessionLocal()

    try:
        job = session.query(Jobs).filter(Jobs.ulid == ulid).first()

        if not job:
            logger.warning(f"Heartbeat: Job {ulid} not found.")
            return 'job_not_found'

        # update the status
        job.status = 'receiving heartbeat'
        
        session.commit()
        logger.debug(f"Heartbeat received and acknowledged for job {ulid}. Status updated to 'receiving heartbeat'.")
        return 'good'
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing heartbeat for {ulid}: {e}", exc_info=True)
        return 'error occured'
    
    finally:
        session.close()
        logger.debug(f"Database session closed for heartbeat_handler for ULID: {ulid}.")
