import json
from typing import List
import requests
import PyPDF2
import io
from docx import Document

from utils.hana_db_connection import (
    batch_insertion_embedding,
    insert_embedding,
    get_hana_db,
)
from utils.embedding import get_embedding


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
        print(chunks)

        preprocessed_chunks = preprocess_text_chunks(chunks)
        print("preprocessed chunks: ", preprocessed_chunks)

        # processing each chunk, vectorizing and storing
        rows = []
        for i, chunk in enumerate(preprocessed_chunks):
            embedding_vector = get_embedding(chunk)

            chunk_metadata[i].update(
                {"chunk_index": i, "chunk_size": len(chunk), "source_url": file_url}
            )

            # serialize metadata and embedding for parameterized batch insert
            metadata_json = json.dumps(chunk_metadata[i])
            embedding_string = str(embedding_vector)

            # building one row: (text, embedding_string, metadata_json)
            rows.append((chunk, embedding_string, metadata_json))

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


def process_file_from_url(file_url: str) -> str:
    try:
        response = requests.get(file_url)
        response.raise_for_status()

        # file extension from url
        file_extension = file_url.split(".")[-1].lower()

        if file_extension == "txt":
            return response.text
        elif file_extension == "pdf":
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            print("pdf successfully downloaded and parsed...")
            return text
        elif file_extension in ["doc", "docx"]:
            doc_file = io.BytesIO(response.content)
            doc = Document(doc_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        else:
            return response.text

    except Exception as e:
        raise Exception(f"failed to process file: {e}")


def preprocess_text_chunks(chunks: List[str]) -> List[str]:
    """
    Preprocess text chunks by removing extra whitespace and applying any other necessary transformations.
    """
    # remove extra whitespace and newlines
    chunks = [chunk.strip().replace("\n", " ") for chunk in chunks]
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    return chunks
