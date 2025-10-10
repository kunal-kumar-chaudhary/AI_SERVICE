from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class FinancialAgentState(TypedDict):
    """
    state for dynamic financial extraction agent
    """

    # input
    input: str 

    # agent memory
    chat_history: Sequence[BaseMessage]

    # scratchpad for tool calls
    intermediate_steps: Annotated[list[tuple], operator.add]

    # iterations control
    iterations: int