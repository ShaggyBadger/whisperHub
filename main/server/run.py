import uvicorn
from app import app
from app.logger import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting server")
    uvicorn.run(app, host="0.0.0.0", port=5000)
