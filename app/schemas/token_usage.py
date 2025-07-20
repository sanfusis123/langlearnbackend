from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TokenUsageBase(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Optional[float] = None


class TokenUsage(TokenUsageBase):
    id: str
    user_id: str
    session_id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class TokenUsageSummary(BaseModel):
    total_tokens: int
    total_cost: float
    model_breakdown: dict[str, dict[str, int]]