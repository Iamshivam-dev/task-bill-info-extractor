from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Automate Accounts PDF processing",
    description="API to upload PDFs, extract text using OCR, and process information.",
    version="1.0.0"
)

# --- Basic Health Check Endpoint ---
@app.get("/", summary="Health Check", response_description="API status message")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    logger.info("Health check endpoint accessed.")
    return {"message": "Server is running."}