import ulid
from .models import Jobs
from pathlib import Path
from . import db

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