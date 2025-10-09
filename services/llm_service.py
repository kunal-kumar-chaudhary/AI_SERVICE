from gen_ai_hub.proxy.native.openai import chat
from dotenv import load_dotenv
from auth.oauth_token import get_access_token_async
import requests
import json
load_dotenv()


# function to get llm response
# def get_llm_response(prompt: str, model_name: str):
#     """
#     args: prompt
#     returns: LLM response augemented using prompt
#     """
#     # response = chat.completions.create(
#     #     model_name=model_name,
#     #     messages=[
#     #         {"role": "system", "content": "You are a helpful assistant."},
#     #         {"role": "user", "content": prompt},
#     #     ],
#     #     temperature=0.0,
#     #     max_tokens=500,
#     # )

#     return "response.choices[0].message.content"

import aiohttp
from auth.oauth_token import get_access_token_async

class LLMService:
    """
    LLM service
    """

    async def get_llm_response_async(prompt: str):
        url = "https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2/inference/deployments/d5903e0d176ce0e4/chat/completions?api-version=2023-05-15"
        access_token = await get_access_token_async()

        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        headers = {
            "AI-Resource-Group": "demo",
            "Accept": "application/json",
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {access_token}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response_data = await response.json()
                return response_data["choices"][0]["message"]["content"]
        

# singleton instance
llm_service = LLMService()