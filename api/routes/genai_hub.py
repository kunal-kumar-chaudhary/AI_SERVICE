from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any

from services.document_processing_service import process_and_embed_file_from_url
from repositories.hana_repository import search_similiar_documents
from auth.oauth_token import get_access_token_async

# Import schemas
from schemas.auth_schemas import TokenResponse
from schemas.embedding_schemas import EmbeddingKGRequest, EmbeddingKGResponse
from schemas.search_schemas import SearchRequest, SearchResponse, SearchResult

# Create router
genai_router = APIRouter()


@genai_router.post("/token", response_model=TokenResponse)
async def access_token():
    """Get access token"""
    try:
        access_token = await get_access_token_async()
        return TokenResponse(access_token=access_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting access token: {str(e)}")


@genai_router.post("/create-store-embedding", response_model=EmbeddingKGResponse)
async def create_and_store_embedding(
    request: EmbeddingKGRequest, 
    background_tasks: BackgroundTasks
) -> EmbeddingKGResponse:
    """
    Create and store embeddings using file URL
    Request parameters:
    - file_url
    - username  
    - doc_type
    """
    try:
        # Processing and embedding the file in background
        background_tasks.add_task(
            process_and_embed_file_from_url,
            request.file_url
        )

        return EmbeddingKGResponse(
            success=True,
            message=f"Successfully processed and embedded document from {request.file_url}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Failed to process and embed documents"
            }
        )


@genai_router.post("/search-similiar-documents", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """
    Search for relevant documents based on the query
    Request parameters:
    - query
    - k: number of results
    - username: filter by username
    """
    try:
        # Using the existing search function
        results = search_similiar_documents(query=request.query, k=request.k)

        # Formatting results  
        formatted_results = []
        if results:
            for doc, score in results:
                if request.username and doc.metadata.get("username") != request.username:
                    continue
                
                result = SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    similarity_score=float(score)
                )
                formatted_results.append(result)

        return SearchResponse(
            success=True,
            query=request.query,
            results=formatted_results,
            count=len(formatted_results)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": str(e),
                "message": "Failed to search documents"
            }
        )