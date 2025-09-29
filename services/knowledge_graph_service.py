import os
import json
from agents.orchestrator import TripletOrchestrator
from services.llm_service import get_llm_response_async
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from repositories.hana_repository import get_hana_db
import asyncio


async def generate_triplets(text_chunk: str):
    """
    Uses an LLM via the Generative AI Hub SDK to extract RDF triplets
    from a given text chunk.

    Args:
        text_chunk: A string containing the unstructured text.

    Returns:
        A list of tuples, where each tuple is a (Subject, Predicate, Object) triplet.
    """
    prompt_for_triplets = f"""
    Extract key factual statements from the text as RDF triplets.

    STRICT REQUIREMENTS:
    1. Return ONLY a valid JSON object
    2. Use exactly this format: {{"triplets": [["subject", "predicate", "object"]]}}
    3. Each triplet must have exactly 3 elements
    4. Use clear, concise predicates (e.g., "is", "has", "uses", "located_in")
    5. Maximum 15 triplets per response
    6. No explanations, no extra text outside JSON

    Text: "{text_chunk}"

    JSON:
    """

    try:

        response_content = await get_llm_response_async(prompt=prompt_for_triplets)
        response_json = json.loads(response_content)
        triplets = response_json.get("triplets", [])
        print(triplets)
        # converting the inner lists to tuples for consistency
        return [tuple(triplet) for triplet in triplets]

    except json.JSONDecodeError:
        print("Failed to parse JSON response from LLM.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


async def convert_corpus_to_triplets_async(
    corpus: list,
    use_orchestrator: bool = True,
) -> List[List[Tuple[str, str, str]]]:
    """
    Convert entire corpus to triplets using async concurrency
    """
    if not corpus:
        return []

    try:

        if use_orchestrator:
            orchestrator = TripletOrchestrator()
            results = await orchestrator.process_corpus(corpus)
            print("results from orchestrator:", results)
            return results
        
        else:
            # Run all LLM calls concurrently
            tasks = [generate_triplets(text) for text in corpus]
            # results contain list of triplets for each chunk
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle errors
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error processing chunk {i}: {result}")
                    processed_results.append([])
                else:
                    processed_results.append(result)

            return processed_results

    except Exception as e:
        print(f"Error in convert_corpus_to_triplets_async: {e}")
        return [[]] * len(corpus)


# sync version for async function for backward compatibility
def convert_corpus_to_triplets(corpus: list) -> List[List[Tuple[str, str, str]]]:
    """Sync wrapper for the async function"""
    return asyncio.run(convert_corpus_to_triplets_async(corpus))


def get_triplets_by_chunks(ref_ids: list, query: str):
    """
    getting triplets from specifc chunks + optional query expansion
    """
    conn = get_hana_db()

    # Build IN clause for ref_ids
    ref_placeholders = ",".join(f"'{ref}'" for ref in ref_ids)

    base_sql = f"""
    SELECT SUBJECT, PREDICATE, OBJECT
    FROM TRIPLE_STORE
    WHERE EMB_REF_ID IN ({ref_placeholders})
    ORDER BY CHUNK_INDEX, ID
    LIMIT 200
    """

    triplets = []
    try:
        df = conn.sql(base_sql).collect()
        for _, row in df.iterrows():
            triplets.append((row["SUBJECT"], row["PREDICATE"], row["OBJECT"]))
    except Exception as e:
        print(f"An error occurred: {e}")

    # optional: expanding with query-related triplets
    if query and triplets:
        expanded = search_related_triplets(
            query, existing_entities=[t[0] for t in triplets[:10]]
        )
        triplets.extend(expanded)

    return triplets


def search_related_triplets(query: str, existing_entities: list, limit: int = 50):
    """
    searching triplets by keyword + entity expansion
    """
    conn = get_hana_db()
    triplets = []

    # keyword search in triplets
    query_clean = query.replace("'", "''")
    keyword_sql = f"""
    SELECT SUBJECT, PREDICATE, OBJECT
    FROM TRIPLE_STORE
    WHERE SUBJECT LIKE '%{query_clean}%'
    OR OBJECT LIKE '%{query_clean}%'
    OR PREDICATE LIKE '%{query_clean}%'
    LIMIT {limit}
    """

    try:
        df = conn.sql(keyword_sql).collect()
        for _, row in df.iterrows():
            triplets.append((row["SUBJECT"], row["PREDICATE"], row["OBJECT"]))
    except Exception as e:
        print(f"error in keyword triplet search: {e}")

    # entity expansion (finding triplets mentioning discovered entities)
    if existing_entities:
        entities_clean = [e.replace("'", "''") for e in existing_entities[:5]]
        entities_placeholders = "','".join(entities_clean)

        expansion_sql = f"""
    SELECT SUBJECT, PREDICATE, OBJECT
    FROM TRIPLE_STORE 
    WHERE SUBJECT IN ('{entities_placeholders}')
    OR OBJECT IN ('{entities_placeholders}')
    LIMIT {limit}
"""

    try:
        df = conn.sql(expansion_sql).collect()
        for _, row in df.iterrows():
            triplets.append((row["SUBJECT"], row["PREDICATE"], row["OBJECT"]))
    except Exception as e:
        print(f"error in entity expansion triplet search: {e}")

    return triplets
