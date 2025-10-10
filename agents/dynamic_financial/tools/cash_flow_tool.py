from langchain.tools import tool
from services.llm_service import llm_service
import json
import re


@tool
async def extract_cash_flow_data(text: str) -> str:
    """
    Extract Cash Flow Statement data: operating, investing, financing cash flows.
    Use this when user asks about cash flow or liquidity.
    """
    prompt = f"""Extract Cash Flow data from this text. Return ONLY valid JSON.

Text: {text[:2000]}

JSON format:
{{"operating_cash_flow": 500000.0, "investing_cash_flow": -200000.0, "financing_cash_flow": -100000.0}}

JSON:"""
    
    response = await llm_service.get_llm_response_async(prompt)
    response = re.sub(r"```json\n?|```\n?", "", response.strip())
    
    try:
        data = json.loads(response)
        return f"Cash Flow extracted: Operating=${data.get('operating_cash_flow', 0):,.0f}, Investing=${data.get('investing_cash_flow', 0):,.0f}, Financing=${data.get('financing_cash_flow', 0):,.0f}"
    except:
        return f"Cash Flow extraction result: {response}"

