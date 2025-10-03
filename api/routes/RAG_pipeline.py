from fastapi import APIRouter, HTTPException
from services.context_service import hybrid_search_context
from services.llm_service import get_llm_response_async
import logging

# Import schemas
from schemas.llm_schemas import RAGChatRequest, RAGChatResponse

# Create router
rag_pipeline_router = APIRouter()
logger = logging.getLogger(__name__)


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

        # searching similiar documents and triplets for building context
        context = await hybrid_search_context(request.query, top_k=request.k, expand_graph=True)
        logger.info(f"Retrieved context: {context}")

        if context == "":
            return RAGChatResponse(
                success=True,
                query=request.query,
                answer="I couldn't find any relevant documents to answer your question."
            )

        answer = await generate_rag_response(request.query, context, request.temperature, request.max_tokens)
        logger.info(f"Generated answer: {answer}")
        
        return RAGChatResponse(
            success=True,
            query=request.query,
            answer=answer
        )

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e)}
        )


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

        response = await get_llm_response_async(prompt=prompt)

        return response

    except Exception as e:
        return f"Error generating response: {str(e)}"