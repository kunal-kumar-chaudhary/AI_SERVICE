from langchain.tools import tool
from services.llm_service import llm_service
import json
import re


@tool
async def extract_pl_data(text: str) -> str:
    """
    extract pl data: revenue, expenses, net income
    use this when user asks about revenue, profit, or income statement
    """

    prompt = f"""Extract P&L data from this text. Return ONLY valid JSON.

Text: {text[:2000]}

JSON format:
{{"revenue": 1000000.0, "expenses": 600000.0, "net_income": 400000.0}}

JSON:"""

    response = await llm_service.get_llm_response_async(prompt)
    response = re.sub(r"```json\n?|```\n?", "", response.strip())

    try:
        data = json.loads(response)
        return f"P&L Data extracted: Revenue=${data.get('revenue', 0):,.0f}, Expenses=${data.get('expenses', 0):,.0f}, Net Income=${data.get('net_income', 0):,.0f}"
    except:
        return f"P&L extraction result: {response}"
