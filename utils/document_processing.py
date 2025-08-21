import json
from typing import List
import requests
import PyPDF2
import io
from docx import Document
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import os
import tempfile

from utils.hana_db_connection import (
    batch_insertion_embedding,
    insert_embedding,
    get_hana_db,
)
from utils.embedding import get_embedding, get_embeddings_batch


def process_and_embed_file_from_url(file_url: str):
    """
    Download file from Supabase, extract text, and store embeddings
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
        # batch-embed all preprocessed chunks
        embeddings = get_embeddings_batch(preprocessed_chunks, max_workers=5)

        # processing each chunk's metadata and building rows
        rows = []
        for i, (chunk, embedding_vector) in enumerate(zip(preprocessed_chunks, embeddings)):
            chunk_metadata[i].update({"chunk_index": i, "chunk_size": len(chunk), "source_url": file_url})
            metadata_json = json.dumps(chunk_metadata[i])
            embedding_string = str(embedding_vector)
            rows.append((chunk, embedding_string, metadata_json))

        # batch insertion in db
        success = batch_insertion_embedding(rows=rows)
        if not success:
            raise Exception("failed to insert embedding into database...")
        else:
            print(
                f"successfully inserted all the embedding and their corresponding embeddings in the database..."
            )
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
        status_forcelist=[429,500,502,503,504],
        allowed_methods=["GET"]
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
                    text = "".join((page.extract_text() or "") for page in pdf_reader.pages)
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
