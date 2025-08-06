from logging import Logger
from urllib.parse import urlencode
from dotenv import load_dotenv
import requests
import os
from flask import jsonify


load_dotenv()

def get_access_token()-> str:
    """
    this function will get the access token from the oauth endpoint
    """
    oauth_endpoint=os.getenv("AICORE_AUTH_URL")
    client_id= os.getenv("AICORE_CLIENT_ID")
    client_secret= os.getenv("AICORE_CLIENT_SECRET")

    print(oauth_endpoint)
    print(client_id)
    print(client_secret)

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
