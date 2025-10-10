from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class FinancialState(BaseModel):
    """Minimal state for financial extraction"""
    
    # Input
    text: str = ""
    
    # Extracted data
    revenue: Optional[float] = None
    expenses: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    equity: Optional[float] = None
    
    # Final output
    financial_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True