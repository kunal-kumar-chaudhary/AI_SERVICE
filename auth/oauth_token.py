from logging import getLogger
from urllib.parse import urlencode
from dotenv import load_dotenv
import requests
import os
from fastapi import HTTPException
import aiohttp

logger = getLogger(__name__)
load_dotenv()

def get_access_token() -> str:
    """Get the access token from the OAuth endpoint"""
    oauth_endpoint = os.getenv("AICORE_AUTH_URL")
    client_id = os.getenv("AICORE_CLIENT_ID")
    client_secret = os.getenv("AICORE_CLIENT_SECRET")

    if not all([oauth_endpoint, client_id, client_secret]):
        raise HTTPException(status_code=500, detail="Missing OAuth environment variables")

    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(oauth_endpoint, data=urlencode(params), headers=headers, timeout=30)
        response.raise_for_status()
        access_token = response.json().get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=500, detail="No access token received")
        
        return access_token

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")


async def get_access_token_async() -> str:
    """Async version using aiohttp"""
    oauth_endpoint = os.getenv("AICORE_AUTH_URL")
    client_id = os.getenv("AICORE_CLIENT_ID")
    client_secret = os.getenv("AICORE_CLIENT_SECRET")

    if not all([oauth_endpoint, client_id, client_secret]):
        raise HTTPException(status_code=500, detail="Missing OAuth environment variables")

    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(oauth_endpoint, data=urlencode(params), headers=headers) as response:
                response.raise_for_status()
                response_data = await response.json()
                access_token = response_data.get("access_token")
                
                if not access_token:
                    raise HTTPException(status_code=500, detail="No access token received")
                
                return access_token

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth error: {str(e)}")