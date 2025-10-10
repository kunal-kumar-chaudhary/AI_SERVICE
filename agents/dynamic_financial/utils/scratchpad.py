def create_scratchpad(intermediate_steps: list) -> str:
    """
    format intermediate steps into readable scratchpad
    """
    if not intermediate_steps:
        return "No intermediate steps taken."
    
    scratchpad = "previous actions:\n"

    for i, (action, observation) in enumerate(intermediate_steps):
        scratchpad += f"\n{i}. Tool: {action.tool}\n"
        scratchpad += f"   Input: {action.tool_input}\n"
        scratchpad += f"   Result: {observation}\n"
    
    return scratchpad

