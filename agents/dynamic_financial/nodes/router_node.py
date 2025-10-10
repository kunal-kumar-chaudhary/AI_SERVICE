from typing import Literal

def route_next(state: dict) -> Literal["run_tool", "final_answer", "__end__"]:
    """
    route to next node baed on oracle's decision
    """

    # checking iteration limit
    if state.get("iterations", 0) >=3:
        return "final_answer"
    
    # getting last oracle response
    intermediate_steps = state.get("intermediate_steps", [])
    if not intermediate_steps:
        return "__end__"
    
    last_step = intermediate_steps[-1]
    agent_action = last_step[0] if isinstance(last_step, tuple) else last_step

    # checking if final answer tool was called
    if hasattr(agent_action, "tool_calls") and agent_action.tool_calls:
        tool_name = agent_action.tool_calls[0]["name"]
        if tool_name == "final_answer":
            return "__end__"
        return "run_tool"
    
    return "__end__"