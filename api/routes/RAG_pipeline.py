from fastapi import APIRouter, HTTPException
from services.context_service import context_service
from services.llm_service import llm_service
import logging
import hashlib

# Import schemas
from schemas.llm_schemas import RAGChatRequest, RAGChatResponse

# Create router
rag_pipeline_router = APIRouter()
logger = logging.getLogger(__name__)


def _make_query_hash(query: str, temperature: float, max_tokens: int) -> str:
    """
    create unique hash for query + parameters
    """
    key_str = f"{query}:{temperature}:{max_tokens}"
    return hashlib.md5(key_str.encode()).hexdigest()[:16]


@rag_pipeline_router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(request: RAGChatRequest) -> RAGChatResponse:
    """
    Complete RAG pipeline: Retrieve + Augment + Generate

    Request body:
    - query: User question (required)
    - k: Number of documents to retrieve (optional, default: 3)
    - username: Filter by user (optional)
    - temperature: LLM temperature (optional, default: 0.1)
    - max_tokens: Response length (optional, default: 500)
    """
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query is required")

        # checking cache first
        cache_key = context_service.cache.make_key(
            "rag_response",
            _make_query_hash(request.query, request.temperature, request.max_tokens),
        )

        cached_response = await context_service.cache.get(cache_key)
        if cached_response:
            logger.info("Cache hit for RAG response")
            cached_response["from_cache"] = True
            return RAGChatResponse(**cached_response)

        logger.info(f"Cache miss for RAG response, processing query: {request.query}")

        # searching similiar documents and triplets for building context
        context = await context_service.hybrid_search_context(
            request.query, top_k=request.k, expand_graph=True
        )

        logger.info(f"Retrieved context: {context}")

        if context == "":
            return RAGChatResponse(
                success=True,
                query=request.query,
                answer="I couldn't find any relevant documents to answer your question.",
            )

        answer = await generate_rag_response(
            request.query, context, request.temperature, request.max_tokens
        )
        response_data = {
            "success": True,
            "query": request.query,
            "answer": answer,
            "context_used": context,
            "from_cache": False
        }

        logger.info(f"Generated answer: {answer}")

        # storing in cache
        await context_service.cache.set(
            cache_key,
            response_data,
            ttl=3600,  # cache for 1 hour
        )

        return RAGChatResponse(**response_data)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


async def generate_rag_response(
    query: str, context: str, temperature: float = 0.1, max_tokens: int = 500
) -> str:
    """
    Generate response using LLM with retrieved context
    """
    try:
        prompt = f"""
        Based on the following context, answer the question:

        Context: 
        {context}

        Question: {query}

        Answer based only on the context provided:
        """

        response = await llm_service.get_llm_response_async(prompt=prompt)

        return response

    except Exception as e:
        return f"Error generating response: {str(e)}"
