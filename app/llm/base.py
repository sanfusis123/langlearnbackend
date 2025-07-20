from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    usage: Dict[str, int]
    model: str
    metadata: Dict[str, Any] = {}


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass