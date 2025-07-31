import requests
import time
import os

def create_configuration(access_token: str, model_name: str) -> str:
    
    ai_api_url = os.getenv("AI_API_URL")
    url = f"{ai_api_url}/v2/lm/configurations"
    
    payload = {
        "name": f"my-embedding-config-{int(time.time() * 1000)}",
        "scenarioId": "foundation-models",
        "executableId": "azure-openai",
        "parameterBindings": [
            {"key": "modelName", "value": model_name},
            {"key": "modelVersion", "value": "latest"}
        ],
        "inputArtifactBindings": []
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "AI-Resource-Group": "demo",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()["id"]
