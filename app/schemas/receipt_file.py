from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from typing import Optional
from pydantic import BaseModel
from ..config.db import Base

class ReceiptFile(Base):
    __tablename__ = "receipt_files"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True, nullable=False)
    file_path = Column(String, unique=True, index=True, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    invalid_reason = Column(String, nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ReceiptFile(id={self.id}, name='{self.file_name}', path='{self.file_path}')>"
    
class ReceiptFileBase(BaseModel):
    file_name: str
    file_path: str
    is_valid: bool = True
    invalid_reason: Optional[str] = None
    is_processed: bool = False