from pydantic import BaseModel
from typing import Dict, Any

class BaseResponse(BaseModel):
    success: bool
    message: str

class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str

class HealthResponse(BaseModel):
    status: str