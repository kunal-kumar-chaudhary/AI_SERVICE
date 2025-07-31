from flask import Blueprint, request, jsonify

# Create a Blueprint for document endpoints
document_bp = Blueprint('document', __name__, url_prefix='/api/documents')


@document_bp.route("/")

@document_bp.route('/', methods=[''])
def get_documents():
    """Get all documents"""
    # Placeholder for document retrieval logic
    documents = [
        {"id": 1, "title": "Sample Document 1", "content": "This is sample content"},
        {"id": 2, "title": "Sample Document 2", "content": "This is another sample"}
    ]
    return jsonify({"documents": documents, "count": len(documents)})

