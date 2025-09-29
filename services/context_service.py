from repositories.hana_repository import search_similiar_documents
from services.knowledge_graph_service import get_triplets_by_chunks

def hybrid_search_context(query: str, top_k: int = 5, expand_graph: bool = True) -> str:
    """
    Hybrid retrieval: vector similarity + graph retrieval
    returns combined textual context for RAG
    """
    # vector search
    vector_results = search_similiar_documents(query, top_k=top_k)

    if not vector_results:
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

