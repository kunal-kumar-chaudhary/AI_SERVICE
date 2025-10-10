from agents.financial.schemas.state_schema import FinancialState

class Aggregator:
    """
    combine all extracted data
    """

    def process(self, state: FinancialState) -> FinancialState:
        """
        aggregate extracted financial data into a single dictionary
        """

        state.financial_data = {
            "income_statement": {
                "revenue": state.revenue,
                "expenses": state.expenses,
                "net_income": state.net_income
            },
            "balance_sheet": {
                "total_assets": state.total_assets,
                "total_liabilities": state.total_liabilities,
                "equity": state.equity
            },
            "errors": state.errors
        }

        return state
