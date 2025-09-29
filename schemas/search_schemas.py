from pydantic import BaseModel
from typing import Optional, List, Dict, Any

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

class HybridSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    expand_graph: Optional[bool] = True
    username: Optional[str] = None

class HybridSearchResponse(BaseModel):
    success: bool
    query: str
    vector_results: List[SearchResult]
    graph_context: Optional[str] = None
    combined_context: str