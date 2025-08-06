from flask import jsonify
from dotenv import load_dotenv
from gen_ai_hub.proxy.native.openai import embeddings


load_dotenv()

def get_embedding(text):
    
    response = embeddings.create(
        input=text,
        model_name = "text-embedding-3-small",
    )
    return response.data[0].embedding




