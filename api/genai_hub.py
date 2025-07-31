from nt import access
from flask import Blueprint, jsonify, requests
import os

from utils.token import get_access_token

genai_bp = Blueprint("genai_hub", __name__, url_prefix="/api/genai")

@genai_bp.route("/token", methods=["POST"])
def access_token(url: str)-> str:
    access_token = get_access_token()
    return jsonify({"access_token": access_token})

@genai_bp.route("/embedding", methods=['POST'])
def create_embedding():
    


