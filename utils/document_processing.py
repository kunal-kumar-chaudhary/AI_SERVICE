import json
from typing import List
import requests
import PyPDF2
import io
from docx import Document
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import os
import uuid
import tempfile
from utils.hana_db_connection import batch_insertion_embedding, insert_triplets

from utils.Knowledge_Graph import convert_corpus_to_triplets
from utils.embedding import get_embeddings_batch


def process_and_create_knowledge_graph_from_doc(file_url: str):
    """
    download file from document storage and create knowledge graph
    """
    try:
        text_content = process_file_from_url(file_url)
        chunks = split_text_into_chunks(text_content)
        preprocessed_chunks = preprocess_text_chunks(chunks)

        # converting corpus to triplets
        all_triplets = convert_corpus_to_triplets(preprocessed_chunks)

        flag = insert_triplets(all_triplets)
        print(f"inserted triplets: {flag}")

    except Exception as e:
        raise Exception(f"failed to process and create knowledge graph: {e}")


def process_and_embed_file_from_url(file_url: str):
    """
    Download file from Supabase, extract text, create embedding and triplets, stores it in database in corresponding tables
    """
    try:
        text_content = process_file_from_url(file_url)
        chunks = split_text_into_chunks(text_content)

        # dictionary to hold metadata
        metadata = {}

        # creating metadata for each chunk
        chunk_metadata = [metadata.copy() for _ in chunks]
        # printing chunks

        preprocessed_chunks = preprocess_text_chunks(chunks)
        print("preprocessed chunks: ", preprocessed_chunks)
        print("point 3", len(preprocessed_chunks))

        # creating reference ids for triple store table to point to embedding table
        ref_ids = [str(uuid.uuid4()) for _ in preprocessed_chunks]

        # batch-embed all preprocessed chunks
        embeddings = get_embeddings_batch(preprocessed_chunks, max_workers=5)

        # creating triplets for all preprocessed chunks
        triplets_per_chunk = convert_corpus_to_triplets(preprocessed_chunks)

        # processing each chunk's metadata and building rows for embdeding insert
        rows = []
        for i, (chunk, embedding_vector) in enumerate(
            zip(preprocessed_chunks, embeddings)
        ):
            chunk_metadata[i].update(
                {"chunk_index": i, "chunk_size": len(chunk), "source_url": file_url, "ref_id": ref_ids[i]}
            )
            metadata_json = json.dumps(chunk_metadata[i])
            embedding_string = str(embedding_vector)
            rows.append((chunk, embedding_string, metadata_json, ref_ids[i]))

        # batch insertion in db
        success = batch_insertion_embedding(rows=rows)
        if not success:
            raise Exception("failed to insert embedding into or ID count mismatch...")
        else:
            print(
                f"successfully inserted all the embedding and their corresponding embeddings in the database..."
            )
        
        # inserting triplets referencing each document_id
        for i, doc_id in enumerate(ref_ids):
            chunk_triplets = triplets_per_chunk[i]
            if chunk_triplets:
                insert_triplets(chunk_triplets, ref_id=doc_id, chunk_index=i)

        # building combined in memory structure (in case we need it downstream)
        combined = []
        for i, doc_id in enumerate(ref_ids):
            combined.append({
                "document_id": doc_id,
                "chunk_index": i,
                "text": preprocessed_chunks[i],
                "embedding": embeddings[i],
                "triplets": triplets_per_chunk[i]
            })  
        print("processed chunks...")
        return combined
        
    except Exception as e:
        raise Exception(f"failed to process and embed file: {e}")


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    split text into overlapping chunks for better embedding
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    print("successfully converted the content into chunks")
    return chunks


# function to create a session with retries (it will handle temporary session)
def _session_with_retries():
    s = requests.session()
    r = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    s.mount("http://", HTTPAdapter(max_retries=r))
    s.mount("https://", HTTPAdapter(max_retries=r))
    return s


def process_file_from_url(file_url: str) -> str:
    """
    Stream download large files with retries and generous timeouts.
    """
    session = _session_with_retries()
    # connect timeout=15s, read timeout=10 minutes
    with session.get(file_url, stream=True, timeout=(15, 600)) as response:
        response.raise_for_status()
        ext = file_url.split("?")[0].split(".")[-1].lower()

        if ext in ["pdf", "doc", "docx"]:
            # writing to temp file to avoid keeping full bytes in memory
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        tmp.write(chunk)
                temp_path = tmp.name
            try:
                if ext == "pdf":
                    pdf_reader = PyPDF2.PdfReader(temp_path)
                    text = "".join(
                        (page.extract_text() or "") for page in pdf_reader.pages
                    )
                else:
                    doc = Document(temp_path)
                    text = "\n".join(p.text for p in doc.paragraphs)
            finally:
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            return text

        # default: treating as text -> stream into memory in chunks
        buf = []
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                buf.append(chunk)
        return b"".join(buf).decode(response.encoding or "utf-8", errors="ignore")


def preprocess_text_chunks(chunks: List[str]) -> List[str]:
    """
    Preprocess text chunks by removing extra whitespace and applying any other necessary transformations.
    """
    # remove extra whitespace and newlines
    chunks = [chunk.strip().replace("\n", " ") for chunk in chunks]
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    return chunks
