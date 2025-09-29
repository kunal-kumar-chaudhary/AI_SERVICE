from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AgentResponse(BaseModel):
    """
    Base response from any agent
    """
    success: bool
    output: Any
    feedback: Optional[str] = None
    quality_score: Optional[float] = None
    error_message: Optional[str] = None

class AnalyzerResponse(AgentResponse):
    """
    Response from the analyzer agent
    """
    triplets: List[List[str]]
    quality_assessment: Dict[str, Any]

class CleanerResponse(AgentResponse):
    """
    Response from semantic cleaner agent
    """
    cleaned_triplets: List[List[str]]
    cleaning_actions: List[str]

class ValidatorResponse(AgentResponse):
    """
    Response from the validator agent
    """
    validated_triplets: List[List[str]]
    validation_issues: List[str]

class RepairResponse(AgentResponse):
    """
    Response from the repair agent
    """
    repaired_json: Dict[str, Any]
    repair_actions: List[str]