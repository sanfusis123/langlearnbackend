from typing import Optional, List
from datetime import datetime, timezone, timedelta
from beanie import PydanticObjectId
from beanie.operators import Or, And, In
from app.models.language_learning import (
    Language, Lesson, Quiz, UserProgress, 
    ConversationFeedback, MeetingAnalysis, MeetingResponseSuggestion,
    UserActivityLog, UserStreak
)
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.token_usage import TokenUsage
from app.services.token_usage import TokenUsageService
from app.schemas.language_learning import (
    LessonCreate, LessonUpdate, QuizCreate, QuizUpdate,
    QuizSubmission, QuizResult, ConversationAnalysisRequest,
    MeetingTranscriptionRequest
)
from app.llm.agents.chat_agent import ChatAgent
import random
from langchain_core.output_parsers import JsonOutputParser
from app.prompt.prompts import analyze_conversation_prompt, analyze_meeting_transcription_prompt, generate_response_suggestions_prompt, generate_custom_scenario_prompt


class LanguageLearningService:
    def __init__(self):
        self.chat_agent = ChatAgent()
    
    @staticmethod
    async def get_languages() -> List[Language]:
        return await Language.find_all().to_list()
    
    @staticmethod
    async def get_language_by_code(code: str) -> Optional[Language]:
        return await Language.find_one(Language.code == code)
    
    # Lesson methods
    async def get_lessons(
        self, 
        user: User,
        language_code: Optional[str] = None,
        level: Optional[str] = None,
        my_lessons_only: bool = False
    ) -> List[Lesson]:
        """Get lessons based on filters"""
        query = []
        
        if my_lessons_only:
            # Only user's lessons
            query.append(Lesson.created_by.id == user.id)
        else:
            # Public lessons OR user's own lessons
            query.append(
                Or(
                    Lesson.is_public == True,
                    And(
                        Lesson.created_by != None,
                        Lesson.created_by.id == user.id
                    )
                )
            )
        
        if language_code:
            language = await self.get_language_by_code(language_code)
            if language:
                query.append(Lesson.language.id == language.id)
        
        if level:
            query.append(Lesson.level == level)
        
        lessons = await Lesson.find(*query).sort(-Lesson.created_at).to_list()
        
        # Fetch links
        for lesson in lessons:
            await lesson.fetch_link(Lesson.language)
            if lesson.created_by:
                await lesson.fetch_link(Lesson.created_by)
        
        return lessons
    
    async def create_lesson(self, user: User, lesson_data: LessonCreate) -> Lesson:
        """Create a new lesson"""
        language = await Language.get(lesson_data.language_id)
        if not language:
            raise ValueError("Language not found")
        
        lesson = Lesson(
            title=lesson_data.title,
            description=lesson_data.description,
            language=language,
            level=lesson_data.level,
            order=lesson_data.order,
            content=lesson_data.content,
            vocabulary=lesson_data.vocabulary,
            grammar_points=lesson_data.grammar_points,
            exercises=lesson_data.exercises,
            estimated_time_minutes=lesson_data.estimated_time_minutes,
            is_public=lesson_data.is_public,
            tags=lesson_data.tags,
            created_by=user
        )
        await lesson.insert()
        await lesson.fetch_link(Lesson.language)
        return lesson
    
    async def get_lesson(self, lesson_id: str, user: User) -> Optional[Lesson]:
        """Get a specific lesson if user has access"""
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            return None
        
        if lesson.created_by:
            await lesson.fetch_link(Lesson.created_by)
        await lesson.fetch_link(Lesson.language)
        
        # Check access: public or owner
        if lesson.is_public or (lesson.created_by and str(lesson.created_by.id) == str(user.id)):
            return lesson
        
        return None
    
    async def update_lesson(
        self, 
        lesson_id: str, 
        user: User, 
        lesson_update: LessonUpdate
    ) -> Optional[Lesson]:
        """Update a lesson (only by creator)"""
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            return None
        
        if lesson.created_by:
            await lesson.fetch_link(Lesson.created_by)
        
        # Only creator can update
        if not lesson.created_by or str(lesson.created_by.id) != str(user.id):
            return None
        
        # Update fields
        for field, value in lesson_update.dict(exclude_unset=True).items():
            setattr(lesson, field, value)
        
        lesson.updated_at = datetime.now(timezone.utc)
        await lesson.save()
        return lesson
    
    async def delete_lesson(self, lesson_id: str, user: User) -> bool:
        """Delete a lesson (only by creator)"""
        lesson = await Lesson.get(lesson_id)
        if not lesson:
            return False
        
        if lesson.created_by:
            await lesson.fetch_link(Lesson.created_by)
        
        # Only creator can delete
        if not lesson.created_by or str(lesson.created_by.id) != str(user.id):
            return False
        
        # Delete associated quizzes
        await Quiz.find(Quiz.lesson.id == PydanticObjectId(lesson_id)).delete()
        
        # Delete user progress
        await UserProgress.find(UserProgress.lesson.id == PydanticObjectId(lesson_id)).delete()
        
        # Delete the lesson
        await lesson.delete()
        return True
    
    # Quiz methods
    async def get_quizzes(
        self,
        user: User,
        language_code: Optional[str] = None,
        level: Optional[str] = None,
        my_quizzes_only: bool = False
    ) -> List[Quiz]:
        """Get quizzes based on filters"""
        query = []
        
        if my_quizzes_only:
            # Only user's quizzes
            query.append(Quiz.created_by.id == user.id)
        else:
            # Public quizzes OR user's own quizzes
            query.append(
                Or(
                    Quiz.is_public == True,
                    And(
                        Quiz.created_by != None,
                        Quiz.created_by.id == user.id
                    )
                )
            )
        
        if language_code:
            language = await self.get_language_by_code(language_code)
            if language:
                query.append(Quiz.language.id == language.id)
        
        if level:
            query.append(Quiz.level == level)
        
        quizzes = await Quiz.find(*query).sort(-Quiz.created_at).to_list()
        
        # Fetch links
        for quiz in quizzes:
            await quiz.fetch_link(Quiz.language)
            if quiz.created_by:
                await quiz.fetch_link(Quiz.created_by)
            if quiz.lesson:
                await quiz.fetch_link(Quiz.lesson)
        
        return quizzes
    
    async def create_quiz(self, user: User, quiz_data: QuizCreate) -> Quiz:
        """Create a new quiz"""
        language = await Language.get(quiz_data.language_id)
        if not language:
            raise ValueError("Language not found")
        
        lesson = None
        if quiz_data.lesson_id:
            lesson = await Lesson.get(quiz_data.lesson_id)
            if not lesson:
                raise ValueError("Lesson not found")
        
        quiz = Quiz(
            lesson=lesson,
            title=quiz_data.title,
            description=quiz_data.description,
            language=language,
            level=quiz_data.level,
            questions=quiz_data.questions,
            passing_score=quiz_data.passing_score,
            time_limit_minutes=quiz_data.time_limit_minutes,
            is_public=quiz_data.is_public,
            tags=quiz_data.tags,
            created_by=user
        )
        await quiz.insert()
        await quiz.fetch_link(Quiz.language)
        return quiz
    
    async def get_quiz(self, quiz_id: str, user: User) -> Optional[Quiz]:
        """Get a specific quiz if user has access"""
        quiz = await Quiz.get(quiz_id)
        if not quiz:
            return None
        
        if quiz.created_by:
            await quiz.fetch_link(Quiz.created_by)
        await quiz.fetch_link(Quiz.language)
        if quiz.lesson:
            await quiz.fetch_link(Quiz.lesson)
        
        # Check access: public or owner
        if quiz.is_public or (quiz.created_by and str(quiz.created_by.id) == str(user.id)):
            return quiz
        
        return None
    
    async def get_quiz_for_lesson(self, lesson_id: str) -> Optional[Quiz]:
        """Get quiz associated with a lesson"""
        quiz = await Quiz.find_one(Quiz.lesson.id == PydanticObjectId(lesson_id))
        if quiz:
            await quiz.fetch_link(Quiz.language)
            if quiz.created_by:
                await quiz.fetch_link(Quiz.created_by)
        return quiz
    
    async def update_quiz(
        self,
        quiz_id: str,
        user: User,
        quiz_update: QuizUpdate
    ) -> Optional[Quiz]:
        """Update a quiz (only by creator)"""
        quiz = await Quiz.get(quiz_id)
        if not quiz:
            return None
        
        if quiz.created_by:
            await quiz.fetch_link(Quiz.created_by)
        
        # Only creator can update
        if not quiz.created_by or str(quiz.created_by.id) != str(user.id):
            return None
        
        # Update fields
        for field, value in quiz_update.dict(exclude_unset=True).items():
            setattr(quiz, field, value)
        
        quiz.updated_at = datetime.now(timezone.utc)
        await quiz.save()
        return quiz
    
    async def delete_quiz(self, quiz_id: str, user: User) -> bool:
        """Delete a quiz (only by creator)"""
        quiz = await Quiz.get(quiz_id)
        if not quiz:
            return False
        
        if quiz.created_by:
            await quiz.fetch_link(Quiz.created_by)
        
        # Only creator can delete
        if not quiz.created_by or str(quiz.created_by.id) != str(user.id):
            return False
        
        await quiz.delete()
        return True
    
    async def submit_quiz(self, user: User, submission: QuizSubmission) -> QuizResult:
        """Submit quiz answers and calculate score"""
        quiz = await Quiz.get(submission.quiz_id)
        if not quiz:
            raise ValueError("Quiz not found")
        
        # Fetch lesson link if exists
        if quiz.lesson:
            await quiz.fetch_link(Quiz.lesson)
        
        # Calculate score
        correct_answers = 0
        feedback = []
        
        for i, answer in enumerate(submission.answers):
            if i < len(quiz.questions):
                question = quiz.questions[i]
                is_correct = answer.get("answer") == question["correct_answer"]
                
                if is_correct:
                    correct_answers += 1
                
                feedback.append({
                    "question": question["question"],
                    "user_answer": answer.get("answer"),
                    "correct_answer": question["correct_answer"],
                    "is_correct": is_correct
                })
        
        total_questions = len(quiz.questions)
        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        passed = score >= quiz.passing_score
        
        # Update quiz statistics
        quiz.attempts_count += 1
        quiz.average_score = (
            (quiz.average_score * (quiz.attempts_count - 1) + score) / quiz.attempts_count
        )
        await quiz.save()
        
        # Log activity
        await self.log_activity(
            user=user,
            activity_type="quiz",
            activity_id=str(quiz.id),
            duration_minutes=submission.time_spent_minutes if hasattr(submission, 'time_spent_minutes') else 10,
            language=quiz.language,
            completed=True,
            score=score
        )
        
        # Update user progress if quiz is linked to a lesson
        if quiz.lesson:
            progress = await UserProgress.find_one(
                UserProgress.user.id == user.id,
                UserProgress.lesson.id == quiz.lesson.id
            )
            
            if progress:
                progress.quiz_scores.append({
                    "quiz_id": str(quiz.id),
                    "score": score,
                    "date": datetime.now(timezone.utc).isoformat()
                })
                
                if passed and not progress.completed:
                    progress.completed = True
                    progress.completion_date = datetime.now(timezone.utc)
                
                await progress.save()
        
        return QuizResult(
            quiz_id=submission.quiz_id,
            score=score,
            passed=passed,
            correct_answers=correct_answers,
            total_questions=total_questions,
            feedback=feedback
        )
    
    # Legacy methods for daily lessons
    @staticmethod
    async def get_daily_lesson(user: User, language_code: str) -> dict:
        """Get daily lesson for a language (legacy method)"""
        language = await Language.find_one(Language.code == language_code)
        if not language:
            raise ValueError(f"Language '{language_code}' not found")
        
        # Get all public lessons for this language
        lessons = await Lesson.find(
            Lesson.language.id == language.id,
            Lesson.is_public == True
        ).sort(Lesson.order).to_list()
        
        if not lessons:
            raise ValueError(f"No lessons available for {language.name}")
        
        # Simple rotation based on day of year
        day_of_year = datetime.now().timetuple().tm_yday
        lesson_index = day_of_year % len(lessons)
        lesson = lessons[lesson_index]
        
        # Fetch related data
        await lesson.fetch_link(Lesson.language)
        
        # Get quiz for this lesson
        quiz = await Quiz.find_one(Quiz.lesson.id == lesson.id)
        if quiz:
            await quiz.fetch_link(Quiz.lesson)
        
        # Get user progress
        progress = await UserProgress.find_one(
            UserProgress.user.id == user.id,
            UserProgress.lesson.id == lesson.id
        )
        
        if progress:
            await progress.fetch_link(UserProgress.user)
            await progress.fetch_link(UserProgress.lesson)
        
        return {
            "lesson": lesson,
            "quiz": quiz,
            "user_progress": progress,
            "is_completed": progress.completed if progress else False
        }
    
    @staticmethod
    async def get_user_progress(user: User, language_code: str) -> List[UserProgress]:
        """Get user's progress for a language"""
        language = await Language.find_one(Language.code == language_code)
        if not language:
            return []
        
        # Get all lessons for this language
        lessons = await Lesson.find(Lesson.language.id == language.id).to_list()
        lesson_ids = [lesson.id for lesson in lessons]
        
        # Get user progress for these lessons
        progress_list = await UserProgress.find(
            UserProgress.user.id == user.id,
            In(UserProgress.lesson.id, lesson_ids)
        ).to_list()
        
        # Fetch lesson details
        for progress in progress_list:
            await progress.fetch_link(UserProgress.lesson)
        
        return progress_list
    
    async def analyze_conversation(
        self, 
        user: User, 
        request: ConversationAnalysisRequest,
        force_new: bool = False
    ) -> ConversationFeedback:
        """Analyze a conversation session"""
        session = await ChatSession.get(request.session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check for existing recent analysis if not forcing new
        # Use force_reanalysis from request if provided, otherwise use force_new parameter
        should_force = request.force_reanalysis or force_new
        if not should_force:
            existing = await self.get_conversation_analysis(user, request.session_id)
            if existing:
                # Check if the analysis is recent (within last hour)
                from datetime import timedelta
                now = datetime.now(timezone.utc)
                # Ensure existing.created_at is timezone-aware
                existing_time = existing.created_at
                if existing_time.tzinfo is None:
                    existing_time = existing_time.replace(tzinfo=timezone.utc)
                
                if now - existing_time < timedelta(hours=1):
                    print(f"Returning existing analysis created at {existing.created_at}")
                    return existing
        
        # Get conversation messages
        messages = await ChatMessage.find(
            ChatMessage.session.id == PydanticObjectId(request.session_id)
        ).sort(ChatMessage.timestamp).to_list()
        
        # Build transcript
        transcript = "\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in messages
        ])
        
        # Analyze with AI
        language = await Language.find_one(Language.code == request.language)
        if not language:
            raise ValueError("Language not found")
        
        analysis_prompt = analyze_conversation_prompt.format(
            language_name=language.name,
            transcript=transcript
        )
        
        result = await self.chat_agent.chat(
            user_input=analysis_prompt,
            chat_history=[],
            temperature=0.3
        )
        
        # Track token usage for conversation analysis
        if "usage" in result and "model" in result:
            token_usage = TokenUsage(
                user=user,
                session=session,  # Link to the conversation session
                model=result["model"],
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                total_tokens=result["usage"]["total_tokens"],
                cost=TokenUsageService.calculate_cost(
                    result["model"],
                    result["usage"]["prompt_tokens"],
                    result["usage"]["completion_tokens"]
                )
            )
            await token_usage.insert()
        
        # Parse AI response and create feedback
        import json
        try:
            json_output_parser = JsonOutputParser()
            feedback_data = json_output_parser.invoke(result["response"])
        except Exception as e:
            print(f"Error parsing conversation analysis: {e}")
            # Enhanced fallback if JSON parsing fails
            feedback_data = {
                "conversation_exchanges": [],
                "mistakes": [],
                "strengths": ["Good effort in the conversation"],
                "suggestions": ["Keep practicing"],
                "improved_sentences": [],
                "vocabulary_suggestions": {
                    "basic_to_advanced": [],
                    "missing_expressions": [],
                    "contextual_vocabulary": []
                },
                "word_bank": {
                    "essential_corrections": [],
                    "recommended_vocabulary": [],
                    "advanced_options": []
                },
                "overall_score": 70,
                "fluency_score": 70,
                "grammar_score": 70,
                "vocabulary_score": 70,
                "pronunciation_score": 70
            }
        
        feedback = ConversationFeedback(
            user=user,
            session=session,
            language=language,
            transcript=transcript,
            conversation_exchanges=feedback_data.get("conversation_exchanges", []),
            mistakes=feedback_data.get("mistakes", []),
            strengths=feedback_data.get("strengths", []),
            suggestions=feedback_data.get("suggestions", []),
            improved_sentences=feedback_data.get("improved_sentences", []),
            vocabulary_suggestions=feedback_data.get("vocabulary_suggestions", {}),
            word_bank=feedback_data.get("word_bank", {}),
            overall_score=feedback_data.get("overall_score", 70),
            fluency_score=feedback_data.get("fluency_score", 70),
            grammar_score=feedback_data.get("grammar_score", 70),
            vocabulary_score=feedback_data.get("vocabulary_score", 70),
            pronunciation_score=feedback_data.get("pronunciation_score", 70)
        )
        
        await feedback.insert()
        return feedback
    
    async def get_conversation_analysis(self, user: User, session_id: str) -> Optional[ConversationFeedback]:
        """Get existing analysis for a conversation session"""
        from beanie import PydanticObjectId
        
        try:
            # Convert session_id to ObjectId
            session_oid = PydanticObjectId(session_id)
            
            # Find the most recent feedback for this session
            # Use find() with sort and limit, then get first result
            feedbacks = await ConversationFeedback.find(
                ConversationFeedback.user.id == user.id,
                ConversationFeedback.session.id == session_oid
            ).sort(-ConversationFeedback.created_at).limit(1).to_list()
            
            if feedbacks and len(feedbacks) > 0:
                feedback = feedbacks[0]
                # Fetch links
                await feedback.fetch_link(ConversationFeedback.language)
                await feedback.fetch_link(ConversationFeedback.session)
                return feedback
            
            return None
        except Exception as e:
            print(f"Error getting conversation analysis: {e}")
            return None
    
    async def analyze_meeting_transcription(
        self,
        user: User,
        request: MeetingTranscriptionRequest
    ) -> MeetingAnalysis:
        """Analyze a meeting transcription"""
        language = await Language.find_one(Language.code == request.language)
        if not language:
            raise ValueError("Language not found")
        
        # Build context for analysis
        context_info = ""
        if request.custom_context:
            context_info = f"\n\nAdditional context from the user: {request.custom_context}\n"
        
        # Analyze with AI
        analysis_prompt = analyze_meeting_transcription_prompt.format(
            language_name=language.name,
            transcript=request.transcription,
            context_info=context_info
        )


        result = await self.chat_agent.chat(
            user_input=analysis_prompt,
            chat_history=[],
            temperature=0.3
        )
        
        # Track token usage for meeting analysis
        if "usage" in result and "model" in result:
            token_usage = TokenUsage(
                user=user,
                session=None,  # No session for meeting analysis
                model=result["model"],
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                total_tokens=result["usage"]["total_tokens"],
                cost=TokenUsageService.calculate_cost(
                    result["model"],
                    result["usage"]["prompt_tokens"],
                    result["usage"]["completion_tokens"]
                ),
                context="meeting_analysis"
            )
            await token_usage.insert()
        
        # Parse AI response
        import json
        try:
            json_output_parser = JsonOutputParser()
            analysis_data = json_output_parser.invoke(result["response"])
            # analysis_data = json.loads(result["response"])
            scores = analysis_data.get("scores", {})
            
            # Extract feedback and suggestions from the new structure
            feedback = analysis_data.get("detailed_feedback", [])
            suggestions = []
            
            # Compile suggestions from improvement roadmap
            roadmap = analysis_data.get("improvement_roadmap", {})
            if roadmap.get("immediate_priorities"):
                suggestions.extend(roadmap["immediate_priorities"])
            if roadmap.get("weekly_practice_goals"):
                suggestions.extend(roadmap["weekly_practice_goals"][:2])  # Add first 2 weekly goals
                
        except Exception as e:
            # Fallback with comprehensive structure
            print(f"Error parsing AI response: {e}")
            analysis_data = {
                "grammar_issues": [],
                "fluency_analysis": {
                    "overall_rating": 0,
                    "coherence_score": 0,
                    "flow_assessment": "Analysis pending",
                    "discourse_effectiveness": "Good use of connecting phrases",
                    "hesitation_patterns": "Minimal hesitations detected",
                    "spontaneity_level": "Natural communication flow"
                },
                "vocabulary_evaluation": {
                    "range_level": "intermediate",
                    "professional_terminology": "Adequate business vocabulary",
                    "technical_accuracy": "Generally accurate",
                    "register_appropriateness": "Appropriate formality",
                    "precision_score": 0,
                    "vocabulary_gaps": ["Advanced business idioms"]
                },
                "meeting_participation": {
                    "contribution_quality": 0,
                    "engagement_level": "Active participation",
                    "information_sharing": "Clear and relevant",
                    "question_quality": "Well-structured questions",
                    "listening_skills": "Good comprehension shown",
                    "meeting_etiquette": "Professional conduct"
                },
                "communication_effectiveness": {
                    "clarity_score": 0,
                    "completeness": "Comprehensive communication",
                    "relevance": "On-topic contributions",
                    "professional_impact": "Positive impression",
                    "leadership_presence": "Developing confidence"
                },
                "organizational_skills": {
                    "structure_score": 0,
                    "prioritization": "Key points highlighted",
                    "time_management": "Concise delivery",
                    "follow_up_clarity": "Clear action items"
                },
                "detailed_feedback": [
                    "Good overall communication skills demonstrated",
                    "Clear articulation of main points",
                    "Professional tone maintained throughout"
                ],
                "improvement_roadmap": {
                    "immediate_priorities": ["Focus on grammar accuracy", "Expand professional vocabulary"],
                    "weekly_practice_goals": ["Practice presenting updates", "Prepare questions in advance"],
                    "monthly_development": ["Join English conversation groups"],
                    "long_term_growth": ["Develop executive presence"],
                    "recommended_resources": ["Business English podcasts", "Professional communication courses"]
                },
                "scores": {
                    "overall_communication": 0,
                    "grammar_accuracy": 0,
                    "fluency": 0,
                    "vocabulary": 75,
                    "meeting_effectiveness": 0,
                    "professional_presence": 0
                },
                "proficiency_assessment": {
                    "current_level": "B2 - Upper Intermediate",
                    "meeting_readiness": "Ready for most professional meetings",
                    "strengths": ["Clear communication", "Good listening skills"],
                    "critical_development_areas": ["Advanced grammar structures", "Executive vocabulary"]
                },
                "next_meeting_preparation": {
                    "focus_areas": ["Grammar accuracy", "Professional phrases"],
                    "practice_exercises": ["Record practice presentations", "Review meeting vocabulary"],
                    "confidence_building": ["Prepare talking points in advance"]
                }
            }
            scores = analysis_data["scores"]
            feedback = analysis_data["detailed_feedback"]
            suggestions = analysis_data["improvement_roadmap"]["immediate_priorities"]
        
        analysis = MeetingAnalysis(
            user=user,
            language=language,
            meeting_name=request.meeting_name,
            transcription=request.transcription,
            custom_context=request.custom_context,
            analysis=analysis_data,
            overall_score=scores.get("overall_communication", 75),
            grammar_score=scores.get("grammar_accuracy", 75),
            fluency_score=scores.get("fluency", 75),
            vocabulary_score=scores.get("vocabulary", 75),
            accuracy_score=scores.get("meeting_effectiveness", 75),  # Using meeting effectiveness as accuracy proxy
            feedback=feedback,
            suggestions=suggestions
        )
        
        await analysis.insert()
        
        # Log activity
        await self.log_activity(
            user=user,
            activity_type="meeting_analysis",
            activity_id=str(analysis.id),
            duration_minutes=max(10, len(request.transcription) // 100),  # Estimate based on transcription length
            language=language,
            completed=True,
            score=analysis.overall_score
        )
        
        return analysis
    
    async def get_user_meeting_analyses(
        self,
        user: User,
        limit: int = 10
    ) -> List[MeetingAnalysis]:
        """Get user's past meeting analyses"""
        analyses = await MeetingAnalysis.find(
            MeetingAnalysis.user.id == user.id
        ).sort(-MeetingAnalysis.created_at).limit(limit).to_list()
        
        # Fetch language links
        for analysis in analyses:
            await analysis.fetch_link(MeetingAnalysis.language)
        
        return analyses
    
    async def generate_response_suggestions(
        self,
        user: User,
        analysis_id: str
    ) -> MeetingResponseSuggestion:
        """Generate improved response suggestions based on meeting analysis"""
        # Get the meeting analysis
        try:
            # Try to convert to PydanticObjectId if needed
            from beanie import PydanticObjectId
            if not isinstance(analysis_id, PydanticObjectId):
                analysis_id = PydanticObjectId(analysis_id)
        except Exception as e:
            print(f"Error converting analysis_id: {e}")
            raise ValueError(f"Invalid analysis ID format: {analysis_id}")
        
        analysis = await MeetingAnalysis.get(analysis_id)
        if not analysis:
            raise ValueError(f"Meeting analysis not found with ID: {analysis_id}")
        
        await analysis.fetch_link(MeetingAnalysis.user)
        if analysis.user.id != user.id:
            raise ValueError("Not authorized to access this analysis")
        
        await analysis.fetch_link(MeetingAnalysis.language)
        
        # Extract user's name from custom context
        user_name = "the user"
        if analysis.custom_context:
            # Try to extract name from context
            import re
            name_patterns = [
                r"(?:my name is|i'm|i am)\s+([a-zA-Z\s]+)",
                r"name:\s*([a-zA-Z\s]+)",
                r"^([a-zA-Z\s]+)\s*(?:here|speaking)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, analysis.custom_context.lower())
                if match:
                    user_name = match.group(1).strip().title()
                    break
        
        # Generate response suggestions prompt
        suggestion_prompt = generate_response_suggestions_prompt.format(
            language_name=analysis.language.name,
            user_name=user_name,
            meeting_name=analysis.meeting_name,
            transcription=analysis.transcription,
            custom_context=analysis.custom_context or "No additional context provided."
        )

        # Get AI suggestions
        result = await self.chat_agent.chat(
            user_input=suggestion_prompt,
            chat_history=[],
            temperature=0.3
        )
        
        # Track token usage for response suggestions
        if "usage" in result and "model" in result:
            token_usage = TokenUsage(
                user=user,
                session=None,  # No session for response suggestions
                model=result["model"],
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                total_tokens=result["usage"]["total_tokens"],
                cost=TokenUsageService.calculate_cost(
                    result["model"],
                    result["usage"]["prompt_tokens"],
                    result["usage"]["completion_tokens"]
                ),
                context="response_suggestions"
            )
            await token_usage.insert()
        
        # Parse AI response
        try:
            json_output_parser = JsonOutputParser()
            suggestion_data = json_output_parser.invoke(result["response"])
        except Exception as e:
            print(f"Error parsing response suggestions: {e}")
            # Fallback data
            suggestion_data = {
                "original_responses": [
                    {
                        "context": "General meeting participation",
                        "original_response": "Unable to extract specific responses",
                        "timing": "Throughout meeting"
                    }
                ],
                "suggested_responses": [
                    {
                        "context": "General meeting participation", 
                        "improved_response": "I'd like to contribute by sharing my perspective on this topic.",
                        "improvements": [
                            "Grammar: Use clear, direct language",
                            "Vocabulary: Professional meeting terminology",
                            "Structure: Organized thought presentation",
                            "Confidence: Assertive but respectful tone"
                        ],
                        "explanation": "This response shows initiative and uses professional language appropriate for meetings."
                    }
                ]
            }
        
        # Create and save response suggestion
        suggestion = MeetingResponseSuggestion(
            user=user,
            meeting_analysis=analysis,
            language=analysis.language,
            original_responses=suggestion_data.get("original_responses", []),
            suggested_responses=suggestion_data.get("suggested_responses", [])
        )
        
        await suggestion.insert()
        return suggestion
    
    # Activity tracking methods
    async def log_activity(
        self,
        user: User,
        activity_type: str,
        duration_minutes: int = 0,
        activity_id: Optional[str] = None,
        language: Optional[Language] = None,
        completed: bool = False,
        score: Optional[int] = None
    ) -> UserActivityLog:
        """Log user activity and update streak"""
        # Create activity log
        activity_log = UserActivityLog(
            user=user,
            activity_type=activity_type,
            activity_id=activity_id,
            duration_minutes=duration_minutes,
            language=language,
            completed=completed,
            score=score
        )
        await activity_log.insert()
        
        # Update user streak
        await self.update_user_streak(user)
        
        return activity_log
    
    async def update_user_streak(self, user: User) -> UserStreak:
        """Update user's streak information"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Get or create user streak
        streak = await UserStreak.find_one(UserStreak.user.id == user.id)
        if not streak:
            streak = UserStreak(
                user=user,
                current_streak=1,
                longest_streak=1,
                last_activity_date=today,
                streak_dates=[today],
                total_days_active=1
            )
            await streak.insert()
            return streak
        
        # Check if activity is on a new day
        if streak.last_activity_date != today:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            
            if streak.last_activity_date == yesterday:
                # Continue streak
                streak.current_streak += 1
                streak.streak_dates.append(today)
            else:
                # Streak broken, start new one
                streak.current_streak = 1
                streak.streak_dates = [today]
            
            streak.total_days_active += 1
            streak.last_activity_date = today
            
            # Update longest streak
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            
            streak.updated_at = datetime.now(timezone.utc)
            await streak.save()
        
        return streak
    
    async def get_user_stats(self, user: User, days: int = 30) -> dict:
        """Get comprehensive user statistics"""
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get activity logs
        activity_logs = await UserActivityLog.find(
            UserActivityLog.user.id == user.id,
            UserActivityLog.date >= since_date
        ).to_list()
        
        # Get streak info
        streak = await UserStreak.find_one(UserStreak.user.id == user.id)
        
        # Calculate stats
        total_time = sum(log.duration_minutes for log in activity_logs)
        lessons_completed = len([log for log in activity_logs if log.activity_type == "lesson" and log.completed])
        quizzes_completed = len([log for log in activity_logs if log.activity_type == "quiz" and log.completed])
        conversations = len([log for log in activity_logs if log.activity_type == "conversation"])
        meetings_analyzed = len([log for log in activity_logs if log.activity_type == "meeting_analysis"])
        
        # Calculate average score from quizzes and meetings
        scores = [log.score for log in activity_logs if log.score is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_practice_time": total_time,
            "lessons_completed": lessons_completed,
            "quizzes_completed": quizzes_completed,
            "conversations": conversations,
            "meetings_analyzed": meetings_analyzed,
            "average_score": round(average_score),
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "total_days_active": streak.total_days_active if streak else 0
        }

    async def generate_custom_scenario(self, user: User, description: str, language: str) -> dict:
        """Generate a custom practice scenario using AI"""
        try:
            # Create prompt for scenario generation
            prompt = generate_custom_scenario_prompt.format(
                description=description,
                language=language
            )

            # Generate scenario using chat agent
            result = await self.chat_agent.chat(
                user_input=prompt,
                chat_history=[],
                temperature=0.8
            )
            
            # Track token usage
            from app.services.token_usage import TokenUsageService
            token_service = TokenUsageService()
            await token_service.track_usage(
                user=user,
                model=result["model"],
                prompt_tokens=result["usage"]["prompt_tokens"],
                completion_tokens=result["usage"]["completion_tokens"],
                total_tokens=result["usage"]["total_tokens"],
                request_type="scenario_generation"
            )
            
            # Parse the JSON response
            import json
            try:
                scenario_data = json.loads(result["response"])
                
                # Save custom scenario to database
                from app.models.language_learning import PracticeScenario
                language_obj = await self.get_language_by_code(language)
                if language_obj:
                    practice_scenario = PracticeScenario(
                        user=user,
                        title=scenario_data.get("title", "Custom Practice Scenario"),
                        description=scenario_data.get("description", description[:200]),
                        role=scenario_data.get("role", "conversation partner"),
                        language=language_obj,
                        scenario_type="custom"
                    )
                    await practice_scenario.insert()
                
                return scenario_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "title": "Custom Practice Scenario",
                    "description": description[:200],
                    "role": "conversation partner"
                }
                
        except Exception as e:
            print(f"Error generating custom scenario: {e}")
            # Return fallback scenario
            return {
                "title": "Custom Practice Scenario",
                "description": description[:200],
                "role": "conversation partner"
            }