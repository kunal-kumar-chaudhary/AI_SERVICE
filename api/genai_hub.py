from typing import Any
from flask import Blueprint, jsonify
import os
from flask import request


from utils.document_processing import process_and_embed_file_from_url
from utils.embedding import get_embedding
from utils.hana_db_connection import insert_embedding, search_similiar_documents
from utils.oauth_token import get_access_token

genai_bp = Blueprint("genai_hub", __name__, url_prefix="/api/genai")


@genai_bp.route("/token", methods=["POST"])
def access_token():
    access_token = get_access_token()
    return jsonify({"access_token": access_token}), 200


# for creating and storing embeddings using juts file url
@genai_bp.route("/create-store-embedding", methods=["POST"])
def create_and_store_embedding() -> Any:
    """
    request parameters:
        - file_url
        - username
        - doc_type
    """

    try:

        if not request.is_json:
            return jsonify({"error": "request must be json"}), 500

        data = request.get_json()
        print("point 0")

        # getting text out of json object inside request
        file_url = data.get("file_url")
        username = data.get("username")
        document_type = data.get("doc_type")

        if not file_url:
            return jsonify({"error": "file_url is required"}), 400
        if not username:
            return jsonify({"error": "username is required"}), 400
        if not document_type:
            return jsonify({"error": "doc_type is required"}), 400

        # creating metadata
        metadata = {"document_type": document_type, "username": username}
        print("point 1")
        # processing and embedding the file
        process_and_embed_file_from_url(
            file_url=file_url
        )

        print("point ----x----")
        return (
            jsonify(
                {
                    "success": True,
                    "message": f"successfully processed and embedded document from {file_url}",
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "message": "failed to process and embed documents",
                }
            ),
            500,
        )


# for just getting embeddings
@genai_bp.route("/search-similiar-documents", methods=["POST"])
def search_documents() -> Any:
    """
    search for relevant documents based on the query
    request parameters:
        - query
        - k: number of results
        - username: filter by username
    """

    try:
        if not request.is_json:
            return jsonify({"error": "request must be json"}), 500

        data = request.json()
        query = data.get("query")
        k = data.get("k", 5)
        username_filter = data.get("username")

        if not query:
            return jsonify({"error": "query is required"}), 400
        
        # using the existing search function
        results = search_similiar_documents(query=query, k=k, username=username)

        # formatting results
        formatted_results = []
        for doc, score in results:
            if username_filter and doc.metadata.get("username") != username:
                continue
            
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "simliarity_score": float(score)
            })
        
        return jsonify({
            "success": True,
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results),
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "failed to search documents",
        }), 500




