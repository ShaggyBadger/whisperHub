from pathlib import Path

class Config:
    # Path to the directories
    AUDIO_FILE_DIR = Path(__file__).parent.parent / 'whisper_worker' / 'audio_files'
    JOB_JSON_DIR = Path(__file__).parent.parent / 'whisper_worker' / 'job_json'
    WORKER_SCRIPT_PATH = Path(__file__).parent.parent / 'whisper_worker' / 'worker.py'