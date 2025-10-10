from langchain.tools import tool
from agents.dynamic_financial.tools import (
    extract_balance_sheet_data,
    extract_cash_flow_data,
    extract_income_statement_data,
    final_answer,
)


class ToolExecutor:
    """
    Execute tools based on oracle's (central node) decision
    """

    def __init__(self):
        self.tools_map = {
            "extract_pl_data": extract_income_statement_data,
            "extract_balance_sheet_data": extract_balance_sheet_data,
            "extract_cash_flow_data": extract_cash_flow_data,
            "final_answer": final_answer,
        }

    async def run(self, state: dict) -> dict:
        """
        execute the tool selected by oracle
        """

        # getting last oracle decision
        intermediate_steps = state.get("intermediate_steps", [])
        last_step = intermediate_steps[-1]
        agent_action = last_step[0]

        # extracting tool call
        tool_call = agent_action.tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]

        # executing tool
        tool = self.tools_map[tool_name]

        text = state["input"].split("DOCUMENT:")[-1].strip()

        if tool_name == "final_answer":
            observation = await tool.ainvoke(tool_input)
        else:
            observation = await tool.ainvoke({"text": text})

        
        # update state
        return {
            "intermediate_steps": [(agent_action, observation)],
            "iterations": state.get("iterations", 0) + 1
        }