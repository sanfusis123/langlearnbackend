from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.user import User, Role, Permission
from app.models.chat import ChatSession, ChatMessage
from app.models.token_usage import TokenUsage
from app.models.language_learning import (
    Language, Lesson, Quiz, UserProgress, 
    ConversationFeedback, MeetingAnalysis, MeetingResponseSuggestion,
    UserActivityLog, UserStreak, PracticeScenario
)


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.DATABASE_URL)
    await init_beanie(
        database=db.client[settings.DATABASE_NAME],
        document_models=[
            User,
            Role,
            Permission,
            ChatSession,
            ChatMessage,
            TokenUsage,
            Language,
            Lesson,
            Quiz,
            UserProgress,
            ConversationFeedback,
            MeetingAnalysis,
            MeetingResponseSuggestion,
            UserActivityLog,
            UserStreak,
            PracticeScenario,
        ],
    )


async def close_mongo_connection():
    db.client.close()