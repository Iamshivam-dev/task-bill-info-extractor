from pydantic import Field, BaseModel

class ValidateRequest(BaseModel):
    receipt_file_id: int = Field(...)