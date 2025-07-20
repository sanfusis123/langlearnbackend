from fastapi import APIRouter
from app.api.endpoints import auth, users, chat, token_usage, language_learning, admin


api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(token_usage.router, prefix="/tokens", tags=["token-usage"])
api_router.include_router(language_learning.router, prefix="/learning", tags=["language-learning"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])