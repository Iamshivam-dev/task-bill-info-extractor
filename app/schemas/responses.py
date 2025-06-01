from pydantic import ConfigDict
from datetime import datetime
from .receipt_file import ReceiptFileBase
from .receipt import ReceiptBase

class ReceiptFileResponse(ReceiptFileBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ReceiptResponse(ReceiptBase):
    id: int
    created_at: datetime
    updated_at: datetime
    purchased_at: datetime | None
    model_config = ConfigDict(from_attributes=True)