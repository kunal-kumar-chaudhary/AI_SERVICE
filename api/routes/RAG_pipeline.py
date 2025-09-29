from fastapi import APIRouter, HTTPException
from typing import Any

from services.llm_service import get_llm_response_async
from services.embedding_service import get_embedding
from repositories.hana_repository import search_similiar_documents, get_all_data

# Import schemas
from schemas.llm_schemas import RAGChatRequest, RAGChatResponse

# Create router
rag_pipeline_router = APIRouter()


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

        query_embedding = get_embedding(request.query)

        # Step 1: Retrieving using existing search function
        results_df = search_similiar_documents(query_embedding=query_embedding, top_k=request.k)

        if results_df is None or results_df.empty:
            return RAGChatResponse(
                success=True,
                query=request.query,
                answer="I couldn't find any relevant documents to answer your question."
            )

        # Step 2: Augmentation - creating context from retrieved documents
        texts = (
            results_df["DOCUMENT_TEXT"].astype(str).tolist()
            if "DOCUMENT_TEXT" in results_df.columns
            else []
        )

        # Building context
        context = "\n\n".join(texts)

        # Step 3: Generating response
        answer = generate_rag_response(request.query, context, request.temperature, request.max_tokens)
        print("Generated answer: ", answer)

        return RAGChatResponse(
            success=True,
            query=request.query,
            answer=answer
        )

    except Exception as e:
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

        # Fixed: get_llm_response only takes prompt parameter
        response = await get_llm_response_async(prompt=prompt)

        return response

    except Exception as e:
        return f"Error generating response: {str(e)}"