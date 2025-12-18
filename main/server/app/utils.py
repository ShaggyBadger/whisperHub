import ulid
from .models import Jobs
from pathlib import Path
from . import db
from sqlalchemy import case


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

        return str(mp3_path)
    
    def store(self):
        # logic to store job in the database
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

            # Save the uploaded file to the designated path
            with open(job_data["file_path"], "wb") as out_file:
                content = self.file.file.read()
                out_file.write(content)

            status_code = "success"
        
        except Exception as e:
            print(f"Error storing job: {e}")
            db_session.rollback()
            status_code = "error"
        
        finally:
            db_session.close()
        
        return status_code

    def get_next_job():
        # logic to request a new job from the database
        db_session = db.SessionLocal()
        try:
            query = db_session.query(Jobs)
            query = query.filter(Jobs.status == 'pending')
            query = query.filter(Jobs.priority_level == 'low')
            query = query.order_by(Jobs.created_at.asc())
            low_priority_job = query.first()

            query = db_session.query(Jobs)
            query = query.filter(Jobs.status == 'pending')
            query = query.filter(Jobs.priority_level == 'high')
            query = query.order_by(Jobs.created_at.asc())
            high_priority_job = query.first()

            job = None
            
            if low_priority_job:
                job = low_priority_job
            
            if high_priority_job:
                job = high_priority_job
            
            if job:
                # update job status and return job
                job.status = "transcribing"
                db_session.commit()

                job_dict = {
                    'ulid': job.ulid,
                    'priority_level': job.priority_level,
                    'file_name': job.file_name,
                    'file_path': job.file_path
                }

                return job_dict
        except Exception as e:
            print(f"Error requesting new job: {e}")
            db_session.rollback()
            return None
        
        finally:
            db_session.close()

def get_file_path_from_db(ulid):
    db_session = db.SessionLocal()

    try:
        query = db_session.query(Jobs)
        query = query.filter(Jobs.ulid == ulid)
        entry = query.first()

        file_path = entry.file_path
        return file_path

    except Exception as e:
        db_session.rollback()
        return None
    
    finally:
        db_session.close()
