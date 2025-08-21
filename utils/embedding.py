from flask import jsonify
from dotenv import load_dotenv
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from gen_ai_hub.proxy.native.openai import embeddings
import time
import sys


load_dotenv()

def get_embedding(text):
    
    response = embeddings.create(
        input=text,
        model_name = "text-embedding-3-small",
    )
    return response.data[0].embedding

def get_embeddings_batch(texts: List[str], max_workers: int = 5) -> List[List[float]]:
    """Create embeddings for a list of texts using parallel single-text requests.

    This does NOT rely on any server-side batch API.

    Args:
        texts: List of input strings to embed.
        max_workers: Number of concurrent requests (1 = sequential).

    Returns:
        List of embedding vectors aligned with the input order.
    """
    if not texts:
        return []

    results: List[List[float]] = [None] * len(texts)  # type: ignore

    def run_single(index: int, text: str) -> Tuple[int, List[float]]:
        print(f"Embedding done : {index}")
        return index, get_embedding(text)

    if max_workers <= 1:
        for i, t in enumerate(texts):
            _, emb = run_single(i, t)
            results[i] = emb
        return results 

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single, i, t) for i, t in enumerate(texts)]
        print(f"[embeddings] submitted {len(futures)} tasks", flush=True)

        completed=0
        for future in as_completed(futures):
            idx, emb = future.result()
            results[idx] = emb
            completed+=1
            print(f"Completed {completed}/{len(texts)} embeddings", flush=True)

    return results 
