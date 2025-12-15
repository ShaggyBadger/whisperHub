# Client API Guide

This document describes how to interact with the WhisperHub FastAPI server, specifically focusing on submitting new transcription jobs.

## Submitting a New Transcription Job (`/new-job`)

This endpoint allows clients to upload an audio file for transcription and specify an optional priority level. The server will store the audio file, create a new job entry in the database, and return a unique Job ID (ULID).

### Endpoint Details

*   **URL:** `/new-job`
*   **Method:** `POST`
*   **Content-Type:** `multipart/form-data`

### Request Parameters

| Parameter Name  | Type           | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Required | 
| :-------------- | :------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------- | 
| `audio_file`    | `File` (binary) | The audio file to be transcribed. Accepted formats include MP3, WAV, FLAC, etc. (FastAPI will handle file upload).                                                                                                                                                                                                                                                                                                                                                                                           | Yes      | 
| `priority_level` | `int`          | An optional integer indicating the priority of the job. Higher numbers typically indicate higher priority. If not provided, a default priority will be assigned by the server (currently 0).                                                                                                                                                                                                                                                                                                                    | No       | 

### Response

The server will respond with a JSON object containing the `job_ulid` if the submission is successful.

*   **Status Code:** `200 OK`
*   **Body:**
    ```json
    {
        "job_ulid": "01HXXXXXXX..."
    }
    ```

### Example (Python using `requests`)

Here's a Python example demonstrating how to send an MP3 file and a priority level to the `/new-job` endpoint.

```python
import requests
import os

# --- Configuration ---
# Replace with the actual URL of your FastAPI server
# This could be 'http://localhost:8000' during local development
# or the IP address of your server in a deployed environment.
FASTAPI_SERVER_URL = "http://192.168.68.66:5000"
NEW_JOB_ENDPOINT = f"{FASTAPI_SERVER_URL}/new-job"

# Path to the audio file you want to upload
AUDIO_FILE_PATH = "path/to/your/audio.mp3" # <--- IMPORTANT: Change this to your actual audio file path

# Optional: Set a priority level for the job
JOB_PRIORITY_LEVEL = 1

# --- Prepare the request ---
# Ensure the audio file exists
if not os.path.exists(AUDIO_FILE_PATH):
    print(f"Error: Audio file not found at {AUDIO_FILE_PATH}")
    exit(1)

# Open the audio file in binary read mode
with open(AUDIO_FILE_PATH, "rb") as audio_file:
    # 'files' dictionary for multipart/form-data upload
    # The key 'audio_file' must match the parameter name in the FastAPI endpoint
    files = {"audio_file": (os.path.basename(AUDIO_FILE_PATH), audio_file, "audio/mpeg")}

    # 'data' dictionary for other form fields (like priority_level)
    # This sends priority_level as a form field, not part of the JSON body
    data = {"priority_level": str(JOB_PRIORITY_LEVEL)}

    print(f"Sending request to: {NEW_JOB_ENDPOINT}")
    print(f"Uploading file: {AUDIO_FILE_PATH}")
    print(f"With priority level: {JOB_PRIORITY_LEVEL}")

    try:
        response = requests.post(NEW_JOB_ENDPOINT, files=files, data=data)

        # Check for successful response
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

        # Parse and print the JSON response
        response_data = response.json()
        print("\nJob submitted successfully!")
        print(f"Received Job ULID: {response_data.get('job_ulid')}")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        print("Please ensure the FastAPI server is running and accessible at the specified URL.")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

```