from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.token_usage import TokenUsage as TokenUsageSchema, TokenUsageSummary
from app.services.token_usage import TokenUsageService


router = APIRouter()


@router.get("/usage", response_model=list[TokenUsageSchema])
async def get_token_usage(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    usage = await TokenUsageService.get_user_usage(
        str(current_user.id),
        start_date,
        end_date
    )
    return usage


@router.get("/usage/summary")
async def get_usage_summary(
    days: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    summary = await TokenUsageService.get_usage_summary(
        str(current_user.id),
        start_date,
        end_date
    )
    
    print(f"Token usage summary for user {current_user.id}: {summary}")
    
    return JSONResponse(content=summary)