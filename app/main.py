from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel
import logging
from .routes import api as api_routes
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .config.db import create_db_and_tables
from .config.config import mkdirs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

    
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    mkdirs()
    yield 


app = FastAPI(
    title="Automate Accounts PDF processing",
    description="API to upload PDFs, extract text using OCR, and process information.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_routes.router)


@app.get("/", summary="Health Check", response_description="API status message")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    logger.info("Health check endpoint accessed.")
    return {"message": "Server is running."}