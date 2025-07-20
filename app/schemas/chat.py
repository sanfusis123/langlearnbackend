from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessage(ChatMessageBase):
    id: str
    session_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    token_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    metadata: Dict[str, Any] = {}


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ChatSession(ChatSessionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    usage: Dict[str, int]
    model: str