# complete RAG pipeline using existing functions

from typing import Any
import os
import requests
from flask import Blueprint, request, jsonify

from utils.hana_db_connection import search_similiar_documents
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
        if not request.is_json():
            return jsonify({"error": "request must be json"}), 400
        
        data = request.json()
        query = data.get("query")
        k = data.get("k", 3)
        username_filter = data.get("username")
        temperature = data.get("temperature", 0.1)
        max_tokens = data.get("max_tokens", 500)

        if not query:
            return jsonify({"error": "query is required"}), 400
        
        # step 1: retreiving using existing search function
        results = search_similiar_documents(query=query, k=k)

        # filtering by name
        if username_filter:
            filtered_results = []
            for doc, score in results:
                if doc.metadata.get("username") == username_filter:
                    filtered_results.append((doc, score))
            results = filtered_results
        
        if not results:
            return jsonify({
                "success": True,
                "query": query,
                "answer": "I couldn't find any relevant documents to answer your question.",
                "sources": []
            }), 200
        
        # step 2: augmentation - creating context from retreived documents
        context = "\n\n".join([doc.page_content for doc, _ in results])
        return context
        # step 3: generating response
        answer = generate_rag_response(query, context, temperature, max_tokens)

        # formatting sources
        sources = [{
            "content": doc.page_content[:200] + "..." if len(doc.page_content)>200 else doc.page_content,
            "metadata": doc.metadata,
            "similarity_score": float(score)
        } for doc, score in results]

        return jsonify({
            "success": True,
            "query": query,
            "answer": answer,
            "sources": sources,
            "retrieval_count": len(results)
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def generate_rag_response(query: str, context: str, temperature: float=0.1, max_tokens: int = 500) -> str:
    """
    generating response using LLM with retrieved context
    """
    try:
        deployment_url = os.getenv("DEPLOYED_LLM_ENDPOINT")
        if not deployment_url:
            return "LLM service not configured"
        
        access_token = get_access_token()

        prompt = f"""
        Based on the following context, answer the question:

        Context: 
        {context}

        Question: {query}

        Answer based only on the context provided:
        """

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "AI-Resource-Group": "demo"
        }

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "gpt-4",
            "max_tokens": max_tokens,
            "temprature": temperature
        }

        response = requests.post(deployment_url, headers=headers, json=payload)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"error generating response: {str(e)}"
