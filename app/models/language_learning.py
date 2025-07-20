from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from beanie import Document, Indexed, Link
from pydantic import Field
from app.models.user import User


class Language(Document):
    code: str  # e.g., "en", "hi", "fr", "ru"
    name: str  # e.g., "English", "Hindi", "French", "Russian"
    native_name: str  # e.g., "English", "हिन्दी", "Français", "Русский"
    
    class Settings:
        name = "languages"
        use_state_management = True


class Lesson(Document):
    title: str
    description: str
    language: Link[Language]
    level: str  # "beginner", "intermediate", "advanced"
    order: int
    content: Dict[str, Any]  # Flexible content structure
    vocabulary: List[Dict[str, str]] = []  # [{"word": "", "translation": "", "pronunciation": ""}]
    grammar_points: List[str] = []
    exercises: List[Dict[str, Any]] = []
    estimated_time_minutes: int
    created_by: Optional[Link[User]] = None  # User who created the lesson
    is_public: bool = False  # Whether the lesson is public or private
    tags: List[str] = []  # Tags for categorization
    likes_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "lessons"
        indexes = [
            [("created_by", 1), ("is_public", 1)],
            [("language", 1), ("is_public", 1)]
        ]


class Quiz(Document):
    lesson: Optional[Link[Lesson]] = None  # Optional - quiz can be standalone
    title: str
    description: Optional[str] = None
    language: Link[Language]
    level: str  # "beginner", "intermediate", "advanced"
    questions: List[Dict[str, Any]]  # [{"question": "", "options": [], "correct_answer": "", "type": ""}]
    passing_score: int = 70
    time_limit_minutes: Optional[int] = None
    created_by: Optional[Link[User]] = None  # User who created the quiz
    is_public: bool = False  # Whether the quiz is public or private
    tags: List[str] = []
    attempts_count: int = 0
    average_score: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "quizzes"
        indexes = [
            [("created_by", 1), ("is_public", 1)],
            [("language", 1), ("is_public", 1)]
        ]


class UserProgress(Document):
    user: Link[User]
    lesson: Link[Lesson]
    completed: bool = False
    completion_date: Optional[datetime] = None
    quiz_scores: List[Dict[str, Any]] = []  # [{"quiz_id": "", "score": 0, "date": ""}]
    time_spent_minutes: int = 0
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "user_progress"
        indexes = [
            [("user", 1), ("lesson", 1)]
        ]


from app.models.chat import ChatSession

class ConversationFeedback(Document):
    user: Link[User]
    session: Link[ChatSession]
    language: Link[Language]
    transcript: str
    user_audio_url: Optional[str] = None
    conversation_exchanges: List[Dict[str, Any]] = []  # AI message → User response analysis
    mistakes: List[Dict[str, Any]] = []  # Enhanced: includes severity, better_words
    strengths: List[str] = []
    suggestions: List[str] = []
    improved_sentences: List[Dict[str, Any]] = []  # Original vs improved sentences
    vocabulary_suggestions: Dict[str, Any] = {}  # Vocabulary enhancement suggestions
    word_bank: Dict[str, List[str]] = {}  # Essential, recommended, advanced words
    overall_score: int  # 0-100
    fluency_score: int
    grammar_score: int
    vocabulary_score: int
    pronunciation_score: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "conversation_feedback"
        indexes = [
            [("user", 1), ("session", 1), ("created_at", -1)]
        ]


class MeetingAnalysis(Document):
    user: Link[User]
    language: Link[Language]
    meeting_name: str  # Name of the meeting or filename
    transcription: str
    custom_context: Optional[str] = None  # User's custom context/message (includes name)
    analysis: Dict[str, Any]  # Detailed analysis results
    overall_score: int
    grammar_score: int
    fluency_score: int
    vocabulary_score: int
    accuracy_score: int
    feedback: List[str] = []
    suggestions: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "meeting_analyses"
        indexes = [
            [("user", 1), ("created_at", -1)]
        ]


class MeetingResponseSuggestion(Document):
    user: Link[User]
    meeting_analysis: Link[MeetingAnalysis]
    language: Link[Language]
    original_responses: List[Dict[str, Any]] = []  # User's original responses from transcript
    suggested_responses: List[Dict[str, Any]] = []  # AI-generated improved responses
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "meeting_response_suggestions"
        indexes = [
            [("user", 1), ("created_at", -1)],
            [("meeting_analysis", 1)]
        ]


class UserActivityLog(Document):
    user: Link[User]
    activity_type: str  # "lesson", "quiz", "conversation", "meeting_analysis"
    activity_id: Optional[str] = None  # ID of the related activity
    duration_minutes: int = 0
    language: Optional[Link[Language]] = None
    completed: bool = False
    score: Optional[int] = None  # For quizzes and analyses
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    
    class Settings:
        name = "user_activity_logs"
        indexes = [
            [("user", 1), ("created_at", -1)],
            [("user", 1), ("date", -1)],
            [("user", 1), ("activity_type", 1)]
        ]


class UserStreak(Document):
    user: Link[User]
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: str  # Format: "YYYY-MM-DD"
    streak_dates: List[str] = []  # List of dates in the current streak
    total_days_active: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "user_streaks"
        indexes = [
            [("user", 1)]
        ]


class PracticeScenario(Document):
    user: Link[User]
    title: str
    description: str
    role: str  # AI role in the scenario
    language: Link[Language]
    scenario_type: str  # "custom", "predefined", "meeting"
    source_id: Optional[str] = None  # ID of source (e.g., meeting_id for meeting scenarios)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "practice_scenarios"
        indexes = [
            [("user", 1), ("created_at", -1)],
            [("user", 1), ("scenario_type", 1)]
        ]