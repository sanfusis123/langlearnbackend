from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Chat Application"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Generate a default secret key if not provided
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # MongoDB settings with defaults
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "fastapi_chat_app"
    
    # OpenAI API key - required for chat functionality
    OPENAI_API_KEY: str = "sk-placeholder"
    REDIS_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()