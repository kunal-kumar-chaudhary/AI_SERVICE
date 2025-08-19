from gen_ai_hub.proxy.native.openai import chat
from dotenv import load_dotenv

load_dotenv()


# function to get llm response
def get_llm_response(prompt: str, model_name: str):
    """
    args: prompt
    returns: LLM response augemented using prompt
    """
    response = chat.completions.create(
        model_name=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=500,
    )

    return response.choices[0].message.content
