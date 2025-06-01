from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from typing import Optional
from pydantic import BaseModel
from ..config.db import Base
from datetime import datetime


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    
    file_path = Column(String, index=True, nullable=False)
    
    purchased_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    merchant_name= Column(String, nullable=True)
    total_amount= Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    
    
class ReceiptBase(BaseModel):
    file_path: str
    purchased_at: datetime | None
    merchant_name: str
    total_amount: float