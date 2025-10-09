from dotenv import load_dotenv
from typing import List, Tuple
import asyncio
import aiohttp
import json
from auth.oauth_token import get_access_token_async

load_dotenv()

class EmbeddingService:
    """
    embedding service
    """

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text
        Args:
            text: input text to embed
        """
        url = "https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2/inference/deployments/d15fa1e81295297d/embeddings?api-version=2024-06-01"
        access_token = await get_access_token_async()
        
        payload = {"model": "text-embedding-3-large", "input": text}
        headers = {
            "AI-Resource-Group": "genai",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return data["data"][0]["embedding"]




    async def get_embeddings_batch(self, texts: List[str], max_workers: int = 5) -> List[List[float]]:
        """
        Create embeddings for a list of texts using asyncio concurrency
        
        Args:
            texts: List of input strings to embed
            max_workers: Maximum concurrent requests (for rate limiting)
            
        Returns:
            List of embedding vectors aligned with the input order
        """
        if not texts:
            return []

        async def run_single(index: int, text: str) -> Tuple[int, List[float]]:
            print(f"Embedding done: {index}")
            embedding = await self.get_embedding(text)
            return index, embedding

        # Use asyncio Semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_workers)
        
        # using semaphore to limit concurrent tasks as it might exceed original api rate limiting
        async def bounded_run_single(index: int, text: str) -> Tuple[int, List[float]]:
            async with semaphore:
                return await run_single(index, text)

        # Creating all tasks
        tasks = [bounded_run_single(i, text) for i, text in enumerate(texts)]
        
        # Runing all tasks concurrently with controlled concurrency
        results_with_indices = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Initialize results array
        results: List[List[float]] = [None] * len(texts)  # type: ignore
        
        # Process results and handle exceptions
        for result in results_with_indices:
            if isinstance(result, Exception):
                print(f"Error in embedding: {result}")
                continue
            
            index, embedding = result
            results[index] = embedding
        
        return results


# global instance for easy import and use
embedding_service = EmbeddingService()

# Sync version for backward compatibility (if needed)
def get_embeddings_batch_sync(texts: List[str], max_workers: int = 5) -> List[List[float]]:
    """Sync wrapper for the async function"""
    return asyncio.run(embedding_service.get_embeddings_batch(texts, max_workers))