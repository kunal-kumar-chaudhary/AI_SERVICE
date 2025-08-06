import requests
import os

# function to create model deployment
def create_deployment(access_token: str, configuration_id: str) -> str:

    ai_api_url = os.getenv("AI_API_URL")

    """
    Create a deployment using the given configuration ID.
    
    Args:
        access_token: OAuth access token
        configuration_id: The configuration ID to deploy
        
    Returns:
        str: Deployment ID
    """

    url = f"{ai_api_url}/v2/lm/deployments"
    payload = {
        "configurationId": configuration_id
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "AI-Resource-Group": "demo",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["id"]