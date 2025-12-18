from . import db
from pathlib import Path
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

# Helper function to get current UTC time
def utcnow():
    return datetime.now(timezone.utc)

class Jobs(db.Base):
    """Holds job info"""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    ulid = Column(String, unique=True, index=True)
    status = Column(String, default="pending") # e.g., pending, processing, completed
    priority_level = Column(String, default="low") # e.g., low, medium, high
    whisper_model = Column(String, default="medium") # option to select a whisper model
    file_name = Column(String)  # Original file name
    file_path = Column(String)  # Path to associated file
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    transcript_path = Column(String, nullable=True) # Stores the path to the transcript file

