from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Link
from pydantic import Field
from app.models.user import User
from app.models.chat import ChatSession


class TokenUsage(Document):
    user: Link[User]
    session: Optional[Link[ChatSession]] = None  # Optional for non-chat contexts
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Optional[float] = None
    context: Optional[str] = None  # e.g., "chat", "meeting_analysis", "response_suggestions"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "token_usage"