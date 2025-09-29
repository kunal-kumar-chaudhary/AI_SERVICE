from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Token related schemas
class TokenResponse(BaseModel):
    access_token: str

# Embedding and Knowledge Graph schemas
class EmbeddingKGRequest(BaseModel):
    file_url: str
    username: str
    doc_type: str

class EmbeddingKGResponse(BaseModel):
    success: bool
    message: str

# Search related schemas
class SearchRequest(BaseModel):
    query: str
    k: Optional[int] = 5
    username: Optional[str] = None

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    similarity_score: float

class SearchResponse(BaseModel):
    success: bool
    query: str
    results: List[SearchResult]
    count: int

# Single embedding schemas
class SingleEmbeddingRequest(BaseModel):
    text: str

class SingleEmbeddingResponse(BaseModel):
    embedding: List[float]

# LLM related schemas
class LLMRequest(BaseModel):
    prompt: str

class LLMResponse(BaseModel):
    response: str

# Common error schema
class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str