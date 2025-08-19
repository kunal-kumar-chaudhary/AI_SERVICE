# complete RAG pipeline using existing functions

from typing import Any
import os
import requests
from flask import Blueprint, request, jsonify

from utils.LLM import get_llm_response
from utils.embedding import get_embedding
from utils.hana_db_connection import search_similiar_documents, get_all_data
from utils.oauth_token import get_access_token

rag_pipeline_bp = Blueprint("rag_pipeline", __name__, url_prefix="/api/rag-pipeline")


@rag_pipeline_bp.route("/chat", methods=["POST"])
def rag_chat() -> Any:
    """
    complete RAG pipeline: Retrieve + Augement + Generate

    request_body:
    {
    "query": "user question".
    "k": 3, // optional, number of documents to retreive
    "username": "john_doe", // optional, filter by user
    "temprature": 0.1, //optional
    "max_token": 500 // optional, response length
    }
    """

    try:
        if not request.is_json:
            return jsonify({"error": "request must be json"}), 400

        data = request.get_json()
        query = data.get("query")
        k = data.get("k", 3)
        username_filter = data.get("username")
        temperature = data.get("temperature", 0.1)
        max_tokens = data.get("max_tokens", 500)

        if not query:
            return jsonify({"error": "query is required"}), 400

        query_embedding = get_embedding(query)

        # step 1: retreiving using existing search function
        results_df = search_similiar_documents(query_embedding=query_embedding, top_k=k)

        if results_df is None or results_df.empty:
            return (
                jsonify(
                    {
                        "success": True,
                        "query": query,
                        "answer": "I couldn't find any relevant documents to answer your question.",
                        "sources": [],
                    }
                ),
                200,
            )

        # step 2: augmentation - creating context from retreived documents
        texts = (
            results_df["DOCUMENT_TEXT"].astype(str).tolist()
            if "DOCUMENT_TEXT" in results_df.columns
            else []
        )
        context = "\n\n".join(texts)

        # step 3: generating response
        answer = generate_rag_response(query, context, temperature, max_tokens)
        print("Generated answer: ", answer)

        return (
            jsonify(
                {
                    "success": True,
                    "query": query,
                    "answer": answer,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def generate_rag_response(
    query: str, context: str, temperature: float = 0.1, max_tokens: int = 500
) -> str:
    """
    generating response using LLM with retrieved context
    """
    try:
        
        prompt = f"""
        Based on the following context, answer the question:

        Context: 
        {context}

        Question: {query}

        Answer based only on the context provided:
        """

        # response = requests.post(deployment_url, headers=headers, json=payload)
        response = get_llm_response(prompt=prompt, model_name="gpt-4o-mini")

        return response

    except Exception as e:
        return f"error generating response: {str(e)}"
