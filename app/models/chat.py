from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from beanie import Document, Link
from pydantic import Field
from app.models.user import User


class ChatSession(Document):
    user: Link[User]
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    metadata: Dict[str, Any] = {}
    
    class Settings:
        name = "chat_sessions"


class ChatMessage(Document):
    session: Link[ChatSession]
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = {}
    token_count: Optional[int] = None
    
    class Settings:
        name = "chat_messages"