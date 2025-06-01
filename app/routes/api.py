from fastapi import APIRouter, Depends, UploadFile, File
from ..services.bill_extractor_service import BillExtractorService
from ..schemas.requests import ValidateRequest
from ..schemas.responses import ReceiptFileResponse, ReceiptResponse
from ..config.db import get_db
from sqlalchemy.orm import Session
from typing import List



router = APIRouter(
    prefix="/api",
    tags=["Apis"]
)

def get_bill_extractor_service(db: Session = Depends(get_db)) -> BillExtractorService:
    return BillExtractorService(db)

@router.post("/upload/", response_model=ReceiptFileResponse)
async def upload(pdf:UploadFile = File(...), service: BillExtractorService = Depends(get_bill_extractor_service)):
    return await service.upload_pdf(pdf)

@router.post("/validate/", response_model=ReceiptFileResponse)
async def validate(request:ValidateRequest, service: BillExtractorService = Depends(get_bill_extractor_service)):
    return await service.validate(request.receipt_file_id)

@router.post("/process", response_model=ReceiptResponse)
def process(request:ValidateRequest, service: BillExtractorService = Depends(get_bill_extractor_service)):
    return service.process(request.receipt_file_id)

@router.get("/receipts", response_model=List[ReceiptResponse])
def receipts(service: BillExtractorService = Depends(get_bill_extractor_service)):
    return service.receipts()

@router.get("/receipts/{id}", response_model=ReceiptResponse)
def receiptDetail(id:int, service: BillExtractorService = Depends(get_bill_extractor_service)):
    return service.getReceipt(id)

