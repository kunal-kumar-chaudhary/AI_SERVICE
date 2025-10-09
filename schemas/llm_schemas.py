from pydantic import BaseModel, Field
from typing import Optional

class LLMRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 500

class LLMResponse(BaseModel):
    response: str

class RAGChatRequest(BaseModel):
    query: str
    k: Optional[int] = 3
    username: Optional[str] = None
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 500

class RAGChatResponse(BaseModel):
    success: bool
    query: str
    answer: str
    context_used: Optional[str] = None
    from_cache: bool = Field(default=False, description="whether answer came from cache")