from typing import List, Dict, Any, Optional, AsyncGenerator
import openai
import tiktoken
from app.llm.base import LLMProvider, LLMResponse
from app.core.config import settings


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4.1-nano"):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            model=response.model,
            metadata={"finish_reason": response.choices[0].finish_reason}
        )
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))