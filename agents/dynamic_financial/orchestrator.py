from langgraph.graph import StateGraph, END
from agents.dynamic_financial.schemas.state_schema import FinancialAgentState
from agents.dynamic_financial.nodes.oracle_node import OracleAgent
from agents.dynamic_financial.nodes.tool_executor_node import ToolExecutor
from agents.dynamic_financial.nodes.router_node import route_next

class DynamicFinancialOrchestrator:
    """
    dynamic multi agent financial extraction orchestrator
    """

    def __init__(self):
        self.oracle = OracleAgent()
        self.tool_executor = ToolExecutor()
        self.graph = self._build_graph()

    def _build_graph(self):
        """
        build dynamic agent graph
        """
        workflow = StateGraph(FinancialAgentState)

        # adding nodes
        workflow.add_node("oracle", self.oracle.run)
        workflow.add_node("run_tool", self.tool_executor.run)

        # setting entry point
        workflow.set_entry_point("oracle")

        # adding conditional routing from oracle
        workflow.add_conditional_edges(
            "oracle",
            route_next,
            {
                "run_tool": "run_tool",
                "__end__": END
            }
        )

        # tool returns to oracle ofr next decision
        workflow.add_edge("run_tool", "oracle")

        return workflow.compile()

    
    async def extract(self, query: str, document_text: str) -> str:
        """
        run dynamic extraction
        """

        # combining query and document
        input_text = f"Query: {query}\n\nDOCUMENT:\n{document_text}"

        initial_state = {
            "input": input_text,
            "chat_history": [],
            "intermediate_steps": [],
            "iterations": 0
        }
        
        # runing the graph
        final_state = await self.graph.ainvoke(initial_state)

        # extracting final answer from intermediate steps
        for step in reversed(final_state.get("intermediate_steps", [])):
            if isinstance(step, tuple) and len(step) == 2:
                action, observation = step
                if hasattr(action, "tool_calls") and action.tool_calls:
                    if action.tool_calls[0]["name"] == "final_answer":
                        return observation
        return "No final answer found."


# global instance
dynamic_financial_orchestrator = DynamicFinancialOrchestrator()
