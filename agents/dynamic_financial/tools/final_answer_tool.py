from langchain.tools import tool
from services.llm_service import llm_service
import json
import re


@tool
def final_answer(report: str) -> str:
    """
    Call this when you have gathered all required financial data.
    Format the collected information into a final structured report.
    """
    return report