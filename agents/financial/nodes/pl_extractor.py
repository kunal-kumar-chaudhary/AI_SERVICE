import json
import re
from agents.financial.schemas.state_schema import FinancialState
from services.llm_service import llm_service


class PLExtractor:
    """Extract Profit & Loss data"""

    async def process(self, state: FinancialState) -> FinancialState:
        """Extract revenue, expenses, net income"""

        prompt = f"""
        Extract financial data from this text. Return ONLY valid JSON, no markdown.

        Text:
        {state.text[:3000]}

        Return JSON:
        {{
            "revenue": 1000000.0,
            "expenses": 600000.0,
            "net_income": 400000.0
        }}

        If a value is not found, use null. Extract numbers without currency symbols.
        JSON:
        """

        try:
            response = await llm_service.get_llm_response_async(prompt)

            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r"```json\n?|```\n?", "", response)

            data = json.loads(response)

            state.revenue = data.get("revenue")
            state.expenses = data.get("expenses")
            state.net_income = data.get("net_income")

        except Exception as e:
            state.errors.append(f"P&L extraction failed: {str(e)}")

        return state
