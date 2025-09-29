from pydantic import BaseModel
from typing import Optional
from schemas.common_schemas import BaseResponse

class DocumentUploadRequest(BaseModel):
    file_url: str
    username: str
    doc_type: str

class DocumentUploadResponse(BaseResponse):
    file_url: Optional[str] = None
    doc_id: Optional[str] = None

class ProcessDocumentRequest(BaseModel):
    file_url: str
    username: str
    doc_type: str

class ProcessDocumentResponse(BaseResponse):
    document_id: Optional[str] = None
    chunks_created: Optional[int] = None