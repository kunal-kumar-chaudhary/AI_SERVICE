from logging import Logger
from urllib.parse import urlencode
from flask import jsonify
import requests
import os

def get_access_token(url: str)-> str:
    """
    this function will get the access token from the oauth endpoint
    """
    oauth_endpoint=os.getenv("AI_CORE_OAUTH_ENDPOINT")
    client_id= os.getenv("AI_CORE_CLIENT_ID")
    client_secret= os.getenv("AI_CORE_CLIENT_SECRET")

    # validating required enviroment variables
    if not all([oauth_endpoint, client_id, client_secret]):
        return jsonify({
            "error": "missing required enviroment variables"
        }), 400

    # request parameters
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    # headers for form-urlencoded content
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(
            oauth_endpoint,
            data=urlencode(params),
            headers=headers
        )

        response.raise_for_status()
        response_data = response.json()
        access_token = response_data.get("access_token")

        if not access_token:
            return jsonify({"error": "no access token"})
        
        return access_token
    except Exception as e:
        Logger.info(f"exception: {str(e)}")

    
