import os
import json
from LLM import get_llm_response
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

def generate_triplets(text_chunk: str):
    """
    Uses an LLM via the Generative AI Hub SDK to extract RDF triplets
    from a given text chunk.

    Args:
        text_chunk: A string containing the unstructured text.

    Returns:
        A list of tuples, where each tuple is a (Subject, Predicate, Object) triplet.
    """
    prompt_for_triplets = f"""
    Analyze the following text and extract the key factual statements as RDF triplets in the format (Subject, Predicate, Object).
    Your response MUST be a single JSON object with one key, "triplets", which contains a list of lists.
    Do not include any explanations or any text outside of the JSON object.

    Text: "{text_chunk}"

    JSON Output:
    """
    
    try:

        response_content = get_llm_response(prompt=prompt_for_triplets, model_name="gpt-4o")
        response_json = json.loads(response_content)
        triplets = response_json.get("triplets", [])

        # converting the inner lists to tuples for consistency
        return [tuple(triplet) for triplet in triplets]

    except json.JSONDecodeError:
        print("Failed to parse JSON response from LLM.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


# function to convert entire corpus list into this triplet format
def convert_corpus_to_triplets(corpus: list) -> list:
    """
    corpus:
        a list of text documents
    returns:
        a list of RDF triplets
    """
    results: List[List[Tuple[str, str, str]]] = [None] * len(corpus)

    def run_single(index: int, text: str) -> list:
        return index, generate_triplets(text)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_single, i, t) for i, t in enumerate(corpus)]

        for future in as_completed(futures):
            index, triplet = future.result()
            results[index] = triplet

    return results