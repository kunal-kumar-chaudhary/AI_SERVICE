from pydantic import BaseModel
from typing import List
from schemas.common_schemas import BaseResponse

class SingleEmbeddingRequest(BaseModel):
    text: str

class SingleEmbeddingResponse(BaseModel):
    embedding: List[float]

class BatchEmbeddingRequest(BaseModel):
    texts: List[str]

class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    count: int

class EmbeddingKGRequest(BaseModel):
    file_url: str
    username: str
    doc_type: str

class EmbeddingKGResponse(BaseResponse):
    processing_started: bool = True