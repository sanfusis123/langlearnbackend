from typing import List, Optional
from datetime import datetime, timedelta
from app.models.token_usage import TokenUsage
from app.models.user import User


class TokenUsageService:
    @staticmethod
    async def get_user_usage(
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[TokenUsage]:
        from beanie import PydanticObjectId
        
        # Build the query using Beanie's query builder
        query = TokenUsage.find(TokenUsage.user.id == PydanticObjectId(user_id))
        
        if start_date:
            query = query.find(TokenUsage.timestamp >= start_date)
        if end_date:
            query = query.find(TokenUsage.timestamp <= end_date)
        
        usage_list = await query.to_list()
        
        # Fetch user links
        for usage in usage_list:
            await usage.fetch_link(TokenUsage.user)
            if hasattr(usage, 'session'):
                await usage.fetch_link(TokenUsage.session)
        
        return usage_list
    
    @staticmethod
    async def get_usage_summary(
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        usage_list = await TokenUsageService.get_user_usage(user_id, start_date, end_date)
        
        total_tokens = 0
        total_cost = 0.0
        model_breakdown = {}
        
        for usage in usage_list:
            total_tokens += usage.total_tokens
            if usage.cost:
                total_cost += usage.cost
            
            if usage.model not in model_breakdown:
                model_breakdown[usage.model] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "count": 0
                }
            
            model_breakdown[usage.model]["prompt_tokens"] += usage.prompt_tokens
            model_breakdown[usage.model]["completion_tokens"] += usage.completion_tokens
            model_breakdown[usage.model]["total_tokens"] += usage.total_tokens
            model_breakdown[usage.model]["count"] += 1
        
        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "model_breakdown": model_breakdown
        }
    
    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = {
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        }
        
        if model not in pricing:
            return 0.0
        
        prompt_cost = (prompt_tokens / 1000) * pricing[model]["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing[model]["completion"]
        
        return prompt_cost + completion_cost