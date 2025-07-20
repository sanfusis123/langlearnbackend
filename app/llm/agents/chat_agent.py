from typing import List, Dict, Any, Optional
from langgraph.graph import Graph, END
from langgraph.graph.graph import CompiledGraph
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.providers.openai_provider import OpenAIProvider


class ChatAgent:
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider or OpenAIProvider()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> CompiledGraph:
        workflow = Graph()
        
        workflow.add_node("process_input", self.process_input)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("store_memory", self.store_memory)
        
        workflow.add_edge("process_input", "generate_response")
        workflow.add_edge("generate_response", "store_memory")
        workflow.add_edge("store_memory", END)
        
        workflow.set_entry_point("process_input")
        
        return workflow.compile()
    
    async def process_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state["user_input"]
        chat_history = state.get("chat_history", [])
        
        messages = []
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": user_input})
        
        state["messages"] = messages
        return state
    
    async def generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state["messages"]
        
        response = await self.llm_provider.generate(
            messages=messages,
            temperature=state.get("temperature", 0.7),
            max_tokens=state.get("max_tokens", None)
        )
        
        state["response"] = response
        state["messages"].append({"role": "assistant", "content": response.content})
        return state
    
    async def store_memory(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state
    
    async def chat(
        self,
        user_input: str,
        chat_history: List[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        initial_state = {
            "user_input": user_input,
            "chat_history": chat_history or [],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        return {
            "response": result["response"].content,
            "usage": result["response"].usage,
            "model": result["response"].model,
            "messages": result["messages"]
        }