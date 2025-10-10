import json
import re
from agents.financial.schemas.state_schema import FinancialState
from services.llm_service import llm_service


class BalanceSheetExtractor:
    """
    extract balance sheet darta
    """

    async def process(self, state: FinancialState) -> FinancialState:
        """
        extract assets, liabilities, equity
        """
        prompt = f"""
Extract balance sheet data from this text. Return ONLY valid JSON, no markdown.

Text:
{state.text[:3000]}

Return JSON:
{{
    "total_assets": 5000000.0,
    "total_liabilities": 3000000.0,
    "equity": 2000000.0
}}

If a value is not found, use null. Extract numbers without currency symbols.
JSON:"""
        try:
            response = await llm_service.get_llm_response_async(prompt)
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r"```json\n?|```\n?", "", response)

            data = json.loads(response)
            state.total_assets = data.get("total_assets")
            state.total_liabilities = data.get("total_liabilities")
            state.equity = data.get("equity")

        except Exception as e:
            state.errors.append(f"Balance sheet extraction failed: {str(e)}")
        
        return state
    
