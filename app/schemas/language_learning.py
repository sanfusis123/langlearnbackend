from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class LanguageBase(BaseModel):
    code: str
    name: str
    native_name: str


class Language(LanguageBase):
    id: str
    
    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    title: str
    description: str
    language_id: str
    level: str
    order: int
    content: Dict[str, Any]
    vocabulary: List[Dict[str, str]] = []
    grammar_points: List[str] = []
    exercises: List[Dict[str, Any]] = []
    estimated_time_minutes: int
    is_public: bool = False
    tags: List[str] = []


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    vocabulary: Optional[List[Dict[str, str]]] = None
    grammar_points: Optional[List[str]] = None
    exercises: Optional[List[Dict[str, Any]]] = None
    estimated_time_minutes: Optional[int] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class Lesson(LessonBase):
    id: str
    created_by_id: Optional[str] = None
    likes_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    lesson_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    language_id: str
    level: str
    questions: List[Dict[str, Any]]
    passing_score: int = 70
    time_limit_minutes: Optional[int] = None
    is_public: bool = False
    tags: List[str] = []


class QuizCreate(QuizBase):
    pass


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None
    passing_score: Optional[int] = None
    time_limit_minutes: Optional[int] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class Quiz(QuizBase):
    id: str
    created_by_id: Optional[str] = None
    attempts_count: int = 0
    average_score: float = 0.0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuizSubmission(BaseModel):
    quiz_id: str
    answers: List[Dict[str, Any]]


class QuizResult(BaseModel):
    quiz_id: str
    score: int
    passed: bool
    correct_answers: int
    total_questions: int
    feedback: List[Dict[str, Any]]


class UserProgressBase(BaseModel):
    user_id: str
    lesson_id: str
    completed: bool = False
    completion_date: Optional[datetime] = None
    quiz_scores: List[Dict[str, Any]] = []
    time_spent_minutes: int = 0


class UserProgress(UserProgressBase):
    id: str
    last_accessed: datetime
    
    class Config:
        from_attributes = True


class ConversationAnalysisRequest(BaseModel):
    session_id: str
    language: str
    audio_url: Optional[str] = None
    force_reanalysis: bool = False


class ConversationAnalysisResponse(BaseModel):
    feedback_id: str
    mistakes: List[Dict[str, Any]]
    strengths: List[str]
    suggestions: List[str]
    overall_score: int
    fluency_score: int
    grammar_score: int
    vocabulary_score: int
    pronunciation_score: int


from pydantic import validator

class MeetingTranscriptionRequest(BaseModel):
    meeting_name: str
    transcription: str
    language: str
    custom_context: str  # Required for new requests - must include user's name
    
    @validator('custom_context')
    def validate_custom_context(cls, v):
        if not v or not v.strip():
            raise ValueError('Custom context is required and must include your name')
        return v.strip()


class MeetingTranscriptionResponse(BaseModel):
    analysis_id: str
    overall_score: int
    grammar_score: int
    fluency_score: int
    vocabulary_score: int
    accuracy_score: int
    feedback: List[str]
    suggestions: List[str]
    detailed_analysis: Dict[str, Any]


class DailyLessonResponse(BaseModel):
    lesson: Lesson
    quiz: Optional[Quiz] = None
    user_progress: Optional[UserProgress] = None
    is_completed: bool = False