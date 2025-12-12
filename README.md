# whisperHub

whisperHub is a Flask-based web application that accepts audio files, transcribes them using a worker process, and provides a status endpoint to check the job progress.

## Project Structure

- `main/server/`: Contains the Flask web server.
  - `app.py`: The main Flask application file.
  - `queue_manager.py`: Manages the job queue.
  - `config.py`: Server configuration.
- `main/whisper_worker/`: Contains the worker process.
  - `worker.py`: The main worker file.
  - `utils.py`: Utility functions for the worker.
  - `audio_files/`: Stores uploaded audio files.
  - `job_json/`: Stores job metadata.
  - `models/`: Stores Whisper models.
- `venvFiles/`: Virtual environment files.
- `requirements.txt`: Project dependencies.

## How it works

1. A client sends a POST request to the `/submit` endpoint with an audio file and metadata.
2. The Flask server generates a unique job ID, saves the audio file and metadata, and adds the job to a queue.
3. The server spawns a `whisper_worker` subprocess to process the job.
4. The `whisper_worker` reads the job data, performs the transcription (placeholder), and sends a POST callback to the server with the result.
5. The server updates the job status.
6. The client can poll the `/status` endpoint to get the job result.

## Setup and Running

1. Install the dependencies: `pip install -r requirements.txt`
2. Run the Flask server: `python main/server/app.py`
