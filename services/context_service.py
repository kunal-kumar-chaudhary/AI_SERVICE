from cache.redis.redis_cache import RedisCache
from repositories.hana_repository import search_similiar_documents
from services.embedding_service import embedding_service
from services.knowledge_graph_service import get_triplets_by_chunks
import logging
logger = logging.getLogger(__name__)

_rag_cache = RedisCache()

class ContextService:
    """
    context service with cache for RAG Pipeline
    """
    
    def __init__(self):
        self.cache = _rag_cache
        
    async def hybrid_search_context(self, query: str, top_k: int = 5, expand_graph: bool = True) -> str:
        """
        Hybrid retrieval: vector similarity + graph retrieval
        returns combined textual context for RAG
        """

        query_embedding = await embedding_service.get_embedding(query)
        # vector search
        vector_results = await search_similiar_documents(query_embedding, top_k=top_k)

        if vector_results is None or vector_results.empty:
            logger.info("No similar documents found.")
            return ""
        
        context_parts = []
        ref_ids = []

        # extracting ref_ids and text from vector results
        for _, row in vector_results.iterrows():
            ref_id = row.get("REF_ID") or row.get("ref_id")
            chunk_text = row.get("DOCUMENT_TEXT", '')
            similiarity = row.get("SIMILARITY", 0)
            
            context_parts.append(f"Chunk (similiarity: {similiarity:.4f}): {chunk_text}")
            if ref_id:
                ref_ids.append(ref_id)
            

        # graph expansion
        if expand_graph and ref_ids:
            graph_context = get_triplets_by_chunks(ref_ids, query)
            if graph_context:
                context_parts.append(f"\nRelated Facts: {graph_context}")
            
        
        return "\n\n".join(context_parts)


# singleton instance
context_service = ContextService()