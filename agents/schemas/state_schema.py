from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class TripletState(BaseModel):
    """
    state management for triplet processing pipeline
    """
    raw_text: str
    initial_triplets: List[List[str]] = []
    cleaned_triplets: List[List[str]] = []
    validated_triplets: List[List[str]] = []
    final_triplets: List[List[str]] = []

    # metadata and tracking
    processing_state: str = "initial"
    error_messages: List[str] = []
    quality_scores: Dict[str, float] = {}
    retry_count: int = 0
    max_retries: int = 3

    # agent outputs
    analyzer_feedback: Optional[str] = None
    cleaner_feedback: Optional[str] = None
    validator_feedback: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
