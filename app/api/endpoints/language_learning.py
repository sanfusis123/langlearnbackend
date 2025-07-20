from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from beanie import PydanticObjectId
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.language_learning import (
    Language as LanguageSchema,
    Lesson as LessonSchema,
    LessonCreate,
    LessonUpdate,
    Quiz as QuizSchema,
    QuizCreate,
    QuizUpdate,
    QuizSubmission,
    QuizResult,
    DailyLessonResponse,
    ConversationAnalysisRequest,
    ConversationAnalysisResponse,
    MeetingTranscriptionRequest,
    MeetingTranscriptionResponse,
    UserProgress as UserProgressSchema
)
from app.services.language_learning import LanguageLearningService
from app.models.language_learning import MeetingAnalysis, MeetingResponseSuggestion, UserActivityLog, UserStreak
import json


router = APIRouter()
language_service = LanguageLearningService()


@router.get("/languages")
async def get_languages():
    languages = await LanguageLearningService.get_languages()
    # Manually serialize the response
    return JSONResponse(content=[
        {
            "id": str(lang.id),
            "code": lang.code,
            "name": lang.name,
            "native_name": lang.native_name
        }
        for lang in languages
    ])


# Lesson endpoints
@router.get("/lessons")
async def get_lessons(
    language_code: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    my_lessons: bool = Query(False),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get lessons. If my_lessons=true, returns only user's lessons.
    Otherwise returns public lessons and user's own lessons.
    """
    lessons = await language_service.get_lessons(
        user=current_user,
        language_code=language_code,
        level=level,
        my_lessons_only=my_lessons
    )
    
    return JSONResponse(content=[
        {
            "id": str(lesson.id),
            "title": lesson.title,
            "description": lesson.description,
            "language_id": str(lesson.language.id),
            "language_code": lesson.language.code,
            "language_name": lesson.language.name,
            "level": lesson.level,
            "order": lesson.order,
            "content": lesson.content,
            "vocabulary": lesson.vocabulary,
            "grammar_points": lesson.grammar_points,
            "exercises": lesson.exercises,
            "estimated_time_minutes": lesson.estimated_time_minutes,
            "is_public": lesson.is_public,
            "tags": lesson.tags,
            "likes_count": lesson.likes_count,
            "created_by_id": str(lesson.created_by.id),
            "created_by_name": lesson.created_by.full_name or lesson.created_by.username,
            "is_mine": str(lesson.created_by.id) == str(current_user.id),
            "created_at": lesson.created_at.isoformat(),
            "updated_at": lesson.updated_at.isoformat()
        }
        for lesson in lessons
    ])


@router.post("/lessons")
async def create_lesson(
    lesson_data: LessonCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new lesson"""
    lesson = await language_service.create_lesson(current_user, lesson_data)
    
    return JSONResponse(content={
        "id": str(lesson.id),
        "title": lesson.title,
        "description": lesson.description,
        "language_id": str(lesson.language.id),
        "level": lesson.level,
        "is_public": lesson.is_public,
        "created_at": lesson.created_at.isoformat()
    })


@router.get("/lessons/{lesson_id}")
async def get_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific lesson"""
    lesson = await language_service.get_lesson(lesson_id, current_user)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get associated quiz if any
    quiz = await language_service.get_quiz_for_lesson(lesson_id)
    
    return JSONResponse(content={
        "id": str(lesson.id),
        "title": lesson.title,
        "description": lesson.description,
        "language_id": str(lesson.language.id),
        "language_code": lesson.language.code,
        "language_name": lesson.language.name,
        "level": lesson.level,
        "order": lesson.order,
        "content": lesson.content,
        "vocabulary": lesson.vocabulary,
        "grammar_points": lesson.grammar_points,
        "exercises": lesson.exercises,
        "estimated_time_minutes": lesson.estimated_time_minutes,
        "is_public": lesson.is_public,
        "tags": lesson.tags,
        "likes_count": lesson.likes_count,
        "created_by_id": str(lesson.created_by.id),
        "created_by_name": lesson.created_by.full_name or lesson.created_by.username,
        "is_mine": str(lesson.created_by.id) == str(current_user.id),
        "quiz": {
            "id": str(quiz.id),
            "title": quiz.title,
            "questions_count": len(quiz.questions),
            "passing_score": quiz.passing_score,
            "time_limit_minutes": quiz.time_limit_minutes
        } if quiz else None,
        "created_at": lesson.created_at.isoformat(),
        "updated_at": lesson.updated_at.isoformat()
    })


@router.put("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: str,
    lesson_update: LessonUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a lesson (only by creator)"""
    lesson = await language_service.update_lesson(lesson_id, current_user, lesson_update)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or you don't have permission")
    
    return JSONResponse(content={"message": "Lesson updated successfully"})


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a lesson (only by creator)"""
    success = await language_service.delete_lesson(lesson_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Lesson not found or you don't have permission")
    
    return JSONResponse(content={"message": "Lesson deleted successfully"})


# Quiz endpoints
@router.get("/quizzes")
async def get_quizzes(
    language_code: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    my_quizzes: bool = Query(False),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get quizzes. If my_quizzes=true, returns only user's quizzes.
    Otherwise returns public quizzes and user's own quizzes.
    """
    quizzes = await language_service.get_quizzes(
        user=current_user,
        language_code=language_code,
        level=level,
        my_quizzes_only=my_quizzes
    )
    
    return JSONResponse(content=[
        {
            "id": str(quiz.id),
            "lesson_id": str(quiz.lesson.id) if quiz.lesson else None,
            "title": quiz.title,
            "description": quiz.description,
            "language_id": str(quiz.language.id),
            "language_code": quiz.language.code,
            "language_name": quiz.language.name,
            "level": quiz.level,
            "questions_count": len(quiz.questions),
            "passing_score": quiz.passing_score,
            "time_limit_minutes": quiz.time_limit_minutes,
            "is_public": quiz.is_public,
            "tags": quiz.tags,
            "attempts_count": quiz.attempts_count,
            "average_score": quiz.average_score,
            "created_by_id": str(quiz.created_by.id),
            "created_by_name": quiz.created_by.full_name or quiz.created_by.username,
            "is_mine": str(quiz.created_by.id) == str(current_user.id),
            "created_at": quiz.created_at.isoformat(),
            "updated_at": quiz.updated_at.isoformat()
        }
        for quiz in quizzes
    ])


@router.post("/quizzes")
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new quiz"""
    quiz = await language_service.create_quiz(current_user, quiz_data)
    
    return JSONResponse(content={
        "id": str(quiz.id),
        "title": quiz.title,
        "description": quiz.description,
        "language_id": str(quiz.language.id),
        "level": quiz.level,
        "is_public": quiz.is_public,
        "created_at": quiz.created_at.isoformat()
    })


@router.get("/quizzes/{quiz_id}")
async def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific quiz"""
    quiz = await language_service.get_quiz(quiz_id, current_user)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return JSONResponse(content={
        "id": str(quiz.id),
        "lesson_id": str(quiz.lesson.id) if quiz.lesson else None,
        "title": quiz.title,
        "description": quiz.description,
        "language_id": str(quiz.language.id),
        "language_code": quiz.language.code,
        "language_name": quiz.language.name,
        "level": quiz.level,
        "questions": quiz.questions,
        "passing_score": quiz.passing_score,
        "time_limit_minutes": quiz.time_limit_minutes,
        "is_public": quiz.is_public,
        "tags": quiz.tags,
        "attempts_count": quiz.attempts_count,
        "average_score": quiz.average_score,
        "created_by_id": str(quiz.created_by.id),
        "created_by_name": quiz.created_by.full_name or quiz.created_by.username,
        "is_mine": str(quiz.created_by.id) == str(current_user.id),
        "created_at": quiz.created_at.isoformat(),
        "updated_at": quiz.updated_at.isoformat()
    })


@router.put("/quizzes/{quiz_id}")
async def update_quiz(
    quiz_id: str,
    quiz_update: QuizUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update a quiz (only by creator)"""
    quiz = await language_service.update_quiz(quiz_id, current_user, quiz_update)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found or you don't have permission")
    
    return JSONResponse(content={"message": "Quiz updated successfully"})


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a quiz (only by creator)"""
    success = await language_service.delete_quiz(quiz_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Quiz not found or you don't have permission")
    
    return JSONResponse(content={"message": "Quiz deleted successfully"})


@router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_active_user)
):
    """Submit quiz answers"""
    result = await language_service.submit_quiz(current_user, submission)
    
    return JSONResponse(content={
        "quiz_id": result.quiz_id,
        "score": result.score,
        "passed": result.passed,
        "correct_answers": result.correct_answers,
        "total_questions": result.total_questions,
        "feedback": result.feedback
    })


# Legacy endpoints for daily lesson (kept for backward compatibility)
@router.get("/lessons/daily/{language_code}")
async def get_daily_lesson(
    language_code: str,
    current_user: User = Depends(get_current_active_user)
):
    try:
        result = await LanguageLearningService.get_daily_lesson(current_user, language_code)
        
        # Manually serialize the response
        response_data = {
            "lesson": {
                "id": str(result["lesson"].id),
                "title": result["lesson"].title,
                "description": result["lesson"].description,
                "language_id": str(result["lesson"].language.id),
                "level": result["lesson"].level,
                "order": result["lesson"].order,
                "content": result["lesson"].content,
                "vocabulary": result["lesson"].vocabulary,
                "grammar_points": result["lesson"].grammar_points,
                "exercises": result["lesson"].exercises,
                "estimated_time_minutes": result["lesson"].estimated_time_minutes,
                "created_at": result["lesson"].created_at.isoformat(),
                "updated_at": result["lesson"].updated_at.isoformat()
            },
            "is_completed": result["is_completed"]
        }
        
        if result.get("quiz"):
            response_data["quiz"] = {
                "id": str(result["quiz"].id),
                "lesson_id": str(result["quiz"].lesson.id) if result["quiz"].lesson else None,
                "title": result["quiz"].title,
                "questions": result["quiz"].questions,
                "passing_score": result["quiz"].passing_score,
                "time_limit_minutes": result["quiz"].time_limit_minutes,
                "created_at": result["quiz"].created_at.isoformat()
            }
        
        if result.get("user_progress"):
            response_data["user_progress"] = {
                "id": str(result["user_progress"].id),
                "user_id": str(result["user_progress"].user.id),
                "lesson_id": str(result["user_progress"].lesson.id),
                "completed": result["user_progress"].completed,
                "completion_date": result["user_progress"].completion_date.isoformat() if result["user_progress"].completion_date else None,
                "quiz_scores": result["user_progress"].quiz_scores,
                "time_spent_minutes": result["user_progress"].time_spent_minutes,
                "last_accessed": result["user_progress"].last_accessed.isoformat()
            }
        
        return JSONResponse(content=response_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/progress/{language_code}")
async def get_user_progress(
    language_code: str,
    current_user: User = Depends(get_current_active_user)
):
    progress = await LanguageLearningService.get_user_progress(current_user, language_code)
    
    # Manually serialize the response
    return JSONResponse(content=[
        {
            "id": str(p.id),
            "lesson_id": str(p.lesson.id),
            "lesson_title": p.lesson.title if hasattr(p.lesson, 'title') else "Unknown",
            "completed": p.completed,
            "completion_date": p.completion_date.isoformat() if p.completion_date else None,
            "quiz_scores": p.quiz_scores,
            "time_spent_minutes": p.time_spent_minutes,
            "last_accessed": p.last_accessed.isoformat()
        }
        for p in progress
    ])


@router.post("/conversation/analyze")
async def analyze_conversation(
    request: ConversationAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    feedback = await language_service.analyze_conversation(current_user, request)
    
    return JSONResponse(content={
        "id": str(feedback.id),
        "feedback_id": str(feedback.id),
        "conversation_exchanges": feedback.conversation_exchanges,
        "mistakes": feedback.mistakes,
        "strengths": feedback.strengths,
        "suggestions": feedback.suggestions,
        "improved_sentences": feedback.improved_sentences,
        "vocabulary_suggestions": feedback.vocabulary_suggestions,
        "word_bank": feedback.word_bank,
        "overall_score": feedback.overall_score,
        "fluency_score": feedback.fluency_score,
        "grammar_score": feedback.grammar_score,
        "vocabulary_score": feedback.vocabulary_score,
        "pronunciation_score": feedback.pronunciation_score
    })


@router.get("/conversation/{session_id}/analysis")
async def get_conversation_analysis(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get existing analysis for a conversation session"""
    feedback = await language_service.get_conversation_analysis(current_user, session_id)
    
    if not feedback:
        return JSONResponse(content=None, status_code=404)
    
    return JSONResponse(content={
        "id": str(feedback.id),
        "feedback_id": str(feedback.id),
        "conversation_exchanges": feedback.conversation_exchanges,
        "mistakes": feedback.mistakes,
        "strengths": feedback.strengths,
        "suggestions": feedback.suggestions,
        "improved_sentences": feedback.improved_sentences,
        "vocabulary_suggestions": feedback.vocabulary_suggestions,
        "word_bank": feedback.word_bank,
        "overall_score": feedback.overall_score,
        "fluency_score": feedback.fluency_score,
        "grammar_score": feedback.grammar_score,
        "vocabulary_score": feedback.vocabulary_score,
        "pronunciation_score": feedback.pronunciation_score,
        "created_at": feedback.created_at.isoformat()
    })


@router.post("/meeting/analyze")
async def analyze_meeting(
    request: MeetingTranscriptionRequest,
    current_user: User = Depends(get_current_active_user)
):
    analysis = await language_service.analyze_meeting_transcription(current_user, request)
    
    return JSONResponse(content={
        "analysis_id": str(analysis.id),
        "meeting_name": analysis.meeting_name,
        "overall_score": analysis.overall_score,
        "grammar_score": analysis.grammar_score,
        "fluency_score": analysis.fluency_score,
        "vocabulary_score": analysis.vocabulary_score,
        "accuracy_score": analysis.accuracy_score,
        "feedback": analysis.feedback,
        "suggestions": analysis.suggestions,
        "detailed_analysis": analysis.analysis
    })


@router.get("/meeting/analyses")
async def get_user_meeting_analyses(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's past meeting analyses"""
    analyses = await language_service.get_user_meeting_analyses(current_user, limit)
    
    return JSONResponse(content={
        "analyses": [
            {
                "id": str(analysis.id),
                "meeting_name": analysis.meeting_name,
                "language": analysis.language.name,
                "language_code": analysis.language.code,
                "overall_score": analysis.overall_score,
                "created_at": analysis.created_at.isoformat(),
                "transcription_preview": analysis.transcription[:200] + "..." if len(analysis.transcription) > 200 else analysis.transcription,
                "has_custom_context": bool(getattr(analysis, 'custom_context', None))
            }
            for analysis in analyses
        ]
    })


@router.get("/meeting/analyses/{analysis_id}")
async def get_meeting_analysis_detail(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed meeting analysis"""
    analysis = await MeetingAnalysis.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    await analysis.fetch_link(MeetingAnalysis.user)
    if analysis.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await analysis.fetch_link(MeetingAnalysis.language)
    
    return JSONResponse(content={
        "id": str(analysis.id),
        "analysis_id": str(analysis.id),  # Add for consistency
        "meeting_name": analysis.meeting_name,
        "language": analysis.language.name,
        "language_code": analysis.language.code,
        "transcription": analysis.transcription,
        "custom_context": analysis.custom_context if hasattr(analysis, 'custom_context') else None,
        "overall_score": analysis.overall_score,
        "grammar_score": analysis.grammar_score,
        "fluency_score": analysis.fluency_score,
        "vocabulary_score": analysis.vocabulary_score,
        "accuracy_score": analysis.accuracy_score,
        "feedback": analysis.feedback,
        "suggestions": analysis.suggestions,
        "detailed_analysis": analysis.analysis,
        "created_at": analysis.created_at.isoformat()
    })


@router.delete("/meeting/analyses/{analysis_id}")
async def delete_meeting_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a meeting analysis"""
    analysis = await MeetingAnalysis.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    await analysis.fetch_link(MeetingAnalysis.user)
    if analysis.user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await analysis.delete()
    
    return JSONResponse(content={"message": "Analysis deleted successfully"})


@router.post("/meeting/analyses/{analysis_id}/response-suggestions")
async def generate_response_suggestions(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Generate improved response suggestions for a meeting analysis"""
    try:
        suggestion = await language_service.generate_response_suggestions(current_user, analysis_id)
        
        return JSONResponse(content={
            "suggestion_id": str(suggestion.id),
            "original_responses": suggestion.original_responses,
            "suggested_responses": suggestion.suggested_responses,
            "created_at": suggestion.created_at.isoformat()
        })
    except ValueError as e:
        print(f"ValueError in generate_response_suggestions: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in generate_response_suggestions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/meeting/analyses/{analysis_id}/response-suggestions")
async def get_response_suggestions(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get response suggestions for a meeting analysis"""
    try:
        # Convert to PydanticObjectId
        from beanie import PydanticObjectId
        try:
            obj_id = PydanticObjectId(analysis_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid analysis ID format: {analysis_id}")
        
        # Find existing suggestions for this analysis
        suggestions = await MeetingResponseSuggestion.find(
            MeetingResponseSuggestion.meeting_analysis.id == obj_id,
            MeetingResponseSuggestion.user.id == current_user.id
        ).sort(-MeetingResponseSuggestion.created_at).to_list()
        
        if not suggestions:
            # First check if the analysis itself exists
            analysis = await MeetingAnalysis.get(analysis_id)
            if not analysis:
                raise HTTPException(status_code=404, detail=f"Meeting analysis not found with ID: {analysis_id}")
            
            # Check if user has access
            await analysis.fetch_link(MeetingAnalysis.user)
            if analysis.user.id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to access this analysis")
            
            # No suggestions exist yet, but that's okay for GET
            raise HTTPException(status_code=404, detail="No response suggestions found for this analysis. Generate them first.")
        
        # Return the most recent suggestion
        suggestion = suggestions[0]
        
        return JSONResponse(content={
            "suggestion_id": str(suggestion.id),
            "original_responses": suggestion.original_responses,
            "suggested_responses": suggestion.suggested_responses,
            "created_at": suggestion.created_at.isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in get_response_suggestions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/meeting/analyses/{analysis_id}/verify")
async def verify_meeting_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Verify if a meeting analysis exists and is accessible"""
    try:
        # Try to get the analysis
        analysis = await MeetingAnalysis.get(analysis_id)
        if not analysis:
            return JSONResponse(content={"exists": False, "message": "Analysis not found"})
        
        # Check ownership
        await analysis.fetch_link(MeetingAnalysis.user)
        if analysis.user.id != current_user.id:
            return JSONResponse(content={"exists": True, "accessible": False, "message": "Not authorized"})
        
        return JSONResponse(content={
            "exists": True,
            "accessible": True,
            "analysis_id": str(analysis.id),
            "meeting_name": analysis.meeting_name,
            "created_at": analysis.created_at.isoformat()
        })
    except Exception as e:
        return JSONResponse(content={"exists": False, "error": str(e)})


@router.get("/stats/dashboard")
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive dashboard statistics for the user"""
    stats = await language_service.get_user_stats(current_user, days)
    return JSONResponse(content=stats)


@router.post("/scenario/generate")
async def generate_custom_scenario(
    request: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Generate a custom practice scenario based on user description"""
    try:
        description = request.get('description', '')
        language = request.get('language', 'en')
        
        if not description.strip():
            raise HTTPException(status_code=400, detail="Description is required")
        
        scenario = await language_service.generate_custom_scenario(current_user, description, language)
        
        return JSONResponse(content={
            "title": scenario.get("title", "Custom Practice Scenario"),
            "description": scenario.get("description", description),
            "role": scenario.get("role", "conversation partner"),
            "language": language
        })
        
    except Exception as e:
        print(f"Error generating custom scenario: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to generate custom scenario")


@router.get("/scenarios/custom")
async def get_custom_scenarios(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's custom scenarios"""
    try:
        from app.models.language_learning import PracticeScenario
        scenarios = await PracticeScenario.find(
            PracticeScenario.user.id == current_user.id,
            PracticeScenario.scenario_type == "custom"
        ).sort(-PracticeScenario.created_at).limit(20).to_list()
        
        # Fetch language links
        for scenario in scenarios:
            await scenario.fetch_link(PracticeScenario.language)
        
        return JSONResponse(content={
            "scenarios": [
                {
                    "id": f"custom_{scenario.id}",
                    "type": "custom",
                    "title": scenario.title,
                    "description": scenario.description,
                    "role": scenario.role,
                    "language": scenario.language.code,
                    "created_at": scenario.created_at.isoformat()
                }
                for scenario in scenarios
            ]
        })
        
    except Exception as e:
        print(f"Error getting custom scenarios: {e}")
        return JSONResponse(content={"scenarios": []})