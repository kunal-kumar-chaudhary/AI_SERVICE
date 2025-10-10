from langchain.tools import tool
from services.llm_service import llm_service
import json
import re


async def extract_balance_sheet_data(text: str) -> str:
    """
    extract balance sheet data: total assets, liabilities, equity.
    use this when user asks about assets, liabilities, equity, or balance sheet
    """

    prompt = f"""Extract Balance Sheet data from this text. Return ONLY valid JSON.

Text: {text[:2000]}

JSON format:
{{"total_assets": 5000000.0, "total_liabilities": 3000000.0, "equity": 2000000.0}}

JSON:"""
    response = await llm_service.get_llm_response_async(prompt)
    response = re.sub(r"```json\n?|```\n?", "", response.strip())
    
    try:
        data = json.loads(response)
        return f"Balance Sheet extracted: Assets=${data.get('total_assets', 0):,.0f}, Liabilities=${data.get('total_liabilities', 0):,.0f}, Equity=${data.get('equity', 0):,.0f}"
    except:
        return f"Balance Sheet extraction result: {response}"
