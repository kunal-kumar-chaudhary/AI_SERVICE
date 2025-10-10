import asyncio
from fastmcp import FastMCP
from services.embedding_service import embedding_service
from services.context_service import context_service
from services.llm_service import llm_service
from repositories.hana_repository import search_similiar_documents
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# creating mcp server instance
mcp = FastMCP("AI-RAG-Service")

@mcp.tool()
async def search_documents(query: str, top_k: int =5) -> str:
    """
    search for similiar documents using semantic vector search

    args:
    - query: user query
    - top_k: number of top documents to retrieve
    """

    # generating embedding for query
    query_embedding = await embedding_service.get_embedding(query)

    # searching similar documents in db
    results = await search_similiar_documents(query_embedding=query_embedding, top_k=top_k)

    if results is None or results.empty:
        return "No similar documents found."
    
    # formatting results
    response = f"found {len(results)} similar documents:\n"

    for idx, row in results.iterrows():
        chunk_text = row.get("DOCUMENT_TEXT", '')
        similarity = row.get("SIMILARITY", 0)
        response += f"Document {idx+1} (similarity: {similarity:.4f}): {chunk_text}\n"

    return response


@mcp.tool()
async def rag_chat(query: str, top_k: int = 3, temperature: float = 0.1) -> str:
    """
    Chat with RAG pipeline - retrieves context and generates answer
    
    Args:
        query: User question
        top_k: Number of documents to retrieve (default: 3)
        temperature: LLM temperature for response generation (default: 0.1)
    """
    # Get context using hybrid search (vector + knowledge graph)
    context = await context_service.hybrid_search_context(
        query, top_k=top_k, expand_graph=True
    )
    
    if not context:
        return "I couldn't find any relevant documents to answer your question."
    
    # Generate answer using LLM
    prompt = f"""Based on the following context, answer the question:

Context: 
{context}

Question: {query}

Answer based only on the context provided:"""
    
    answer = await llm_service.get_llm_response_async(prompt=prompt)
    
    return answer

@mcp.tool()
async def generate_embedding(text: str) -> str:
    """
    Generate embedding vector for given text
    
    Args:
        text: Text to generate embedding for
    """
    embedding = await embedding_service.get_embedding(text)
    return f"Generated embedding vector with {len(embedding)} dimensions (first 5 values: {embedding[:5]})"


# running server
if __name__ == "__main__":
    mcp.run()