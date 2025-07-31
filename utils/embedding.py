import os
from typing import Any
from . import generate_access_token
import requests


# this functin will create embedding using the deployment url from enviroment file
def generateEmbedding(text: str) -> Any:
    deployment_url = os.getenv("DEPLOYED_MODEL_ENDPOINT")
    access_token = generate_access_token()

    """
    args: 
        - configurationId
        - deploymentId
    return:
        - embedding vector
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "AI-Resource-Group": "demo",
    }

    payload = {"input": text, "model": "text-embedding-3-small"}

    try:
        response = requests.post(deployment_url, headers=headers, json=payload)
        embedding = response.json()["data"][0]["embedding"]
        return embedding

    except Exception as e:
        raise e
