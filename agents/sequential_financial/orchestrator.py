from langgraph.graph import StateGraph, END
from agents.sequential_financial.schemas.state_schema import FinancialState
from agents.sequential_financial.nodes.pl_extractor import PLExtractor
from agents.sequential_financial.nodes.balance_sheet_agent import BalanceSheetExtractor
from agents.sequential_financial.nodes.aggregator_agent import Aggregator

class FinancialOrchestrator:
    """Minimal financial extraction orchestrator"""
    
    def __init__(self):
        self.pl_extractor = PLExtractor()
        self.bs_extractor = BalanceSheetExtractor()
        self.aggregator = Aggregator()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build extraction workflow"""
        workflow = StateGraph(FinancialState)
        
        # Add nodes
        workflow.add_node("extract_pl", self.pl_extractor.process)
        workflow.add_node("extract_bs", self.bs_extractor.process)
        workflow.add_node("aggregate", self.aggregator.process)
        
        # Define flow
        workflow.set_entry_point("extract_pl")
        workflow.add_edge("extract_pl", "extract_bs")
        workflow.add_edge("extract_bs", "aggregate")
        workflow.add_edge("aggregate", END)
        
        return workflow.compile()
    
    async def extract(self, text: str) -> dict:
        """Run extraction pipeline"""
        initial_state = FinancialState(text=text)
        final_state = await self.graph.ainvoke(initial_state)
        return final_state.financial_data


# Global instance
financial_orchestrator = FinancialOrchestrator()