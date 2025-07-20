from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import json
import asyncio
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.token_usage import TokenUsage
from app.services.chat import ChatService
from app.services.language_learning import LanguageLearningService
from app.llm.agents.chat_agent import ChatAgent
from jose import JWTError, jwt
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def get_scenario_context(scenario_id: str, scenario_type: str, user, language: str):
    """Get scenario context based on type and ID"""
    logger.info(f"=== FETCHING SCENARIO CONTEXT ===")
    logger.info(f"Scenario ID: {scenario_id}")
    logger.info(f"Scenario Type: {scenario_type}")
    logger.info(f"Language: {language}")
    logger.info(f"User: {user.username}")
    
    try:
        if scenario_type == "predefined":
            # Predefined scenarios - only store basic info, not full context
            scenarios = {
                "job_interview": {
                    "title": "Job Interview",
                    "role": "interviewer",
                    "summary": "conducting a job interview"
                },
                "restaurant": {
                    "title": "Restaurant Conversation", 
                    "role": "restaurant server",
                    "summary": "helping customer with menu and orders"
                },
                "business_meeting": {
                    "title": "Business Meeting",
                    "role": "business colleague",
                    "summary": "discussing project updates and collaboration"
                },
                "travel": {
                    "title": "Travel & Tourism",
                    "role": "travel assistant",
                    "summary": "helping traveler with information and bookings"
                },
                "shopping": {
                    "title": "Shopping",
                    "role": "shop assistant",
                    "summary": "helping customer find and purchase products"
                },
                "doctor_visit": {
                    "title": "Doctor Visit",
                    "role": "doctor",
                    "summary": "medical consultation with patient"
                }
            }
            context = scenarios.get(scenario_id)
            logger.info(f"Predefined scenario found: {context}")
            return context
            
        elif scenario_type == "meeting":
            # Get meeting analysis for context - only summary, not full transcription
            from app.models.language_learning import MeetingAnalysis
            meeting_id = scenario_id.replace("meeting_", "")
            analysis = await MeetingAnalysis.get(meeting_id)
            
            if analysis:
                await analysis.fetch_link(MeetingAnalysis.user)
                if analysis.user.id == user.id:
                    # Create a brief summary instead of sending full transcription
                    meeting_summary = f"meeting about {analysis.meeting_name}"
                    if len(analysis.transcription) > 200:
                        meeting_summary += f" - topic: {analysis.transcription[:200]}..."
                    
                    return {
                        "title": analysis.meeting_name,
                        "role": "meeting participant",
                        "summary": meeting_summary
                    }
            
        elif scenario_type == "custom":
            # Get custom scenario from database
            from app.models.language_learning import PracticeScenario
            custom_id = scenario_id.replace("custom_", "")
            scenario = await PracticeScenario.get(custom_id)
            
            if scenario:
                await scenario.fetch_link(PracticeScenario.user)
                if scenario.user.id == user.id:
                    return {
                        "title": scenario.title,
                        "role": scenario.role,
                        "summary": scenario.description
                    }
            
            # Fallback if scenario not found
            return {
                "title": "Custom Scenario",
                "role": "conversation partner", 
                "summary": "custom practice scenario"
            }
            
    except Exception as e:
        logger.error(f"Error getting scenario context: {e}")
    
    return None


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


async def get_current_user_websocket(token: str) -> Optional[User]:
    """Authenticate user from WebSocket connection"""
    try:
        logger.info(f"Attempting to decode JWT token")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        logger.info(f"JWT decoded successfully, username: {username}")
        if username is None:
            logger.error("No username in JWT payload")
            return None
        
        user = await User.find_one(User.username == username)
        if user:
            logger.info(f"User found: {user.username}")
        else:
            logger.error(f"User not found for username: {username}")
        return user
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


async def websocket_conversation_endpoint(
    websocket: WebSocket,
    token: str,
    language: str = "en",
    session_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    scenario_type: Optional[str] = None
):
    logger.info(f"WebSocket connection attempt with token: {token[:20] if token else 'None'}... language: {language}")
    
    try:
        if not token:
            logger.error("No token provided")
            await websocket.close(code=1008, reason="No token provided")
            return
        
        # Test database connection
        try:
            from app.models.user import User
            count = await User.count()
            logger.info(f"Database connection test: {count} users found")
        except Exception as db_error:
            logger.error(f"Database connection failed: {db_error}")
            await websocket.close(code=1011, reason="Database connection failed")
            return
        
        user = await get_current_user_websocket(token)
        if not user:
            logger.error("Authentication failed for token")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        logger.info(f"User {user.username} authenticated successfully")
        
        await manager.connect(websocket, str(user.id))
    except Exception as e:
        logger.error(f"Error during WebSocket authentication: {e}")
        try:
            await websocket.close(code=1011, reason=f"Server error: {str(e)}")
        except:
            pass
        return
    chat_service = ChatService()
    chat_agent = ChatAgent()
    
    # Get scenario context if provided
    scenario_context = None
    if scenario_id and scenario_type:
        logger.info(f"=== WEBSOCKET SCENARIO REQUEST ===")
        logger.info(f"Client requested scenario: ID={scenario_id}, Type={scenario_type}")
        scenario_context = await get_scenario_context(scenario_id, scenario_type, user, language)
        if scenario_context:
            logger.info(f"Scenario context retrieved successfully")
            logger.info(f"Scenario title: {scenario_context.get('title', 'N/A')}")
            logger.info(f"Scenario role: {scenario_context.get('role', 'N/A')}")
        else:
            logger.warning(f"Failed to retrieve scenario context")
    else:
        logger.info("No scenario requested for this conversation")
    
    try:
        # Create or get session
        if session_id:
            session = await ChatSession.get(session_id)
            if not session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                await websocket.close(code=1008)
                return
            
            # Fetch user link and verify ownership
            await session.fetch_link(ChatSession.user)
            if str(session.user.id) != str(user.id):
                await websocket.send_json({
                    "type": "error",
                    "message": "Not authorized to access this session"
                })
                await websocket.close(code=1008)
                return
                
            logger.info(f"Continuing existing session {session.id} for user {user.username}")
            await websocket.send_json({
                "type": "session_resumed",
                "session_id": str(session.id),
                "message": "Resuming previous conversation"
            })
        else:
            from app.schemas.chat import ChatSessionCreate
            logger.info(f"Creating new session for user {user.username} (ID: {user.id})")
            
            # Prepare session metadata with scenario information
            session_metadata = {}
            if scenario_context:
                session_metadata = {
                    "scenario": {
                        "id": scenario_id,
                        "type": scenario_type,
                        "title": scenario_context.get("title", ""),
                        "description": scenario_context.get("summary", ""),
                        "role": scenario_context.get("role", "")
                    },
                    "language": language
                }
            
            # Create session with metadata
            session_data = ChatSessionCreate(
                title=f"Voice Conversation - {language.upper()}{' - ' + scenario_context.get('title', '') if scenario_context else ''}",
                metadata=session_metadata
            )
            session = await chat_service.create_session(user, session_data)
            logger.info(f"Created session {session.id} for user {user.id} with scenario: {scenario_id if scenario_id else 'None'}")
            await websocket.send_json({
                "type": "session_created",
                "session_id": str(session.id)
            })
        
        # Get conversation history
        messages = await chat_service.get_session_messages(str(session.id))
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        await websocket.send_json({
            "type": "ready",
            "message": "Connected. Start speaking..."
        })


        
        while True:
            try:
                # Receive message from WebSocket with timeout
                message = await asyncio.wait_for(websocket.receive(), timeout=300.0)  # 5 minute timeout
                logger.info(f"Received WebSocket message type: {message['type']}")
                
                if message["type"] == "websocket.disconnect":
                    logger.info("Client disconnected")
                    break
                elif message["type"] == "websocket.receive":
                    if "text" in message:
                        try:
                            data = json.loads(message["text"])
                            logger.info(f"Parsed JSON message: {data}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON received: {message['text']}, error: {e}")
                            try:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Invalid JSON format"
                                })
                            except:
                                logger.error("Could not send error message - WebSocket already closed")
                            continue
                    else:
                        logger.warning("Received non-text message")
                        continue
                else:
                    logger.warning(f"Unknown message type: {message['type']}")
                    continue
                
            except asyncio.TimeoutError:
                logger.info("WebSocket timeout, sending keepalive")
                try:
                    await websocket.send_json({
                        "type": "keepalive",
                        "message": "Connection is alive"
                    })
                except:
                    logger.error("Could not send keepalive - WebSocket already closed")
                    break
                continue
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {e}")
                break
            
            if data["type"] == "voice_input":
                user_text = data.get("text", "").strip()
                logger.info(f"Processing voice input: '{user_text}'")
                
                if user_text:
                    try:
                        # Send acknowledgment
                        # await websocket.send_json({
                        #     "type": "user_message_received",
                        #     "text": user_text
                        # })
                        # logger.info("Sent user message acknowledgment")
                        
                        # Generate AI response
                        logger.info("Generating AI response...")
                        
                        # Prepare chat history with scenario context
                        enhanced_history = history_dicts.copy() if history_dicts else []
                        
                        # Add scenario context as a system message if we have one
                        if scenario_context:
                            logger.info(f"=== WEBSOCKET SCENARIO SYSTEM PROMPT ===")
                            logger.info(f"Checking if system message needed for scenario")
                            
                            # Check if system message already exists
                            has_system_message = any(msg.get("role") == "system" for msg in enhanced_history)
                            logger.info(f"System message already exists: {has_system_message}")
                            
                            if not has_system_message:
                                logger.info(f"Adding scenario system prompt to conversation")
                                logger.info(f"Scenario role: {scenario_context['role']}")
                                logger.info(f"Scenario summary: {scenario_context['summary']}")
                                
                                # Add scenario context as the first message
                                system_message = {
                                    "role": "system",
                                    "content": f"""You are taking on the role of {scenario_context['role']} in a {language} conversation practice. The topic is: {scenario_context['summary']}.

                                    Your goal is to simulate a natural, human-like conversation. Speak as a real person would: vary your sentence length, use natural pauses, and react to what the user says. Sometimes answer briefly, sometimes expand — just like people do.

                                    Ask follow-up questions. Make observations. Respond with a mix of clarity and personality. Avoid sounding repetitive or scripted.

                                    You are here to help the user get comfortable using {language} in realistic situations. Keep things practical, friendly, and dynamic. Stay in character and keep the flow going.

                                    Don't over-explain. Don't dominate the conversation. Let the user lead when it makes sense, and gently guide them when they need help.
                                    
                                    Your response should not be too long. Try to keep it concise and engaging.
                                    """
                                    }

                                enhanced_history.insert(0, system_message)
                                logger.info(f"System prompt added to enhanced history")
                                logger.info(f"System prompt length: {len(system_message['content'])} characters")
                            else:
                                logger.info("System message already exists, not adding another")
                        else:
                            logger.info("No scenario context, proceeding with regular conversation")
                        
                        result = await chat_agent.chat(
                            user_input=user_text,
                            chat_history=enhanced_history,
                            temperature=0.8
                        )
                        logger.info(f"AI response generated: {result['response'][:100]}...")
                        
                        # Save user message
                        user_message = ChatMessage(
                            session=session,
                            role="user",
                            content=user_text,
                            token_count=chat_agent.llm_provider.count_tokens(user_text)
                        )
                        await user_message.insert()
                        logger.info(f"Saved user message to session {session.id}")
                        
                        # Save assistant message
                        assistant_message = ChatMessage(
                            session=session,
                            role="assistant",
                            content=result["response"],
                            token_count=result["usage"]["completion_tokens"],
                            metadata={"model": result["model"]}
                        )
                        await assistant_message.insert()
                        logger.info(f"Saved assistant message to session {session.id}")
                        
                        # Update history
                        history_dicts.append({"role": "user", "content": user_text})
                        history_dicts.append({"role": "assistant", "content": result["response"]})
                        
                        # Save token usage
                        token_usage = TokenUsage(
                            user=user,
                            session=session,
                            model=result["model"],
                            prompt_tokens=result["usage"]["prompt_tokens"],
                            completion_tokens=result["usage"]["completion_tokens"],
                            total_tokens=result["usage"]["total_tokens"]
                        )
                        await token_usage.insert()
                        logger.info(f"Saved token usage: {result['usage']['total_tokens']} tokens for model {result['model']}")
                        
                        # Send AI response
                        await websocket.send_json({
                            "type": "assistant_message",
                            "text": result["response"],
                            "usage": result["usage"]
                        })
                        logger.info("Sent AI response to client")
                        
                    except Exception as e:
                        logger.error(f"Error processing voice input: {e}")
                        import traceback
                        traceback.print_exc()
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Error processing your message: {str(e)}"
                            })
                        except:
                            logger.error("Could not send error message - WebSocket already closed")
                else:
                    logger.warning("Empty voice input received")
                
            elif data["type"] == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "message": "pong"
                })
                
            elif data["type"] == "analyze_conversation":
                # Analyze conversation without ending it
                language_service = LanguageLearningService()
                from app.schemas.language_learning import ConversationAnalysisRequest
                
                # Get force_reanalysis from WebSocket data if provided
                force_reanalysis = data.get("force_reanalysis", False)
                
                analysis_request = ConversationAnalysisRequest(
                    session_id=str(session.id),
                    language=language,
                    force_reanalysis=force_reanalysis
                )
                
                try:
                    feedback = await language_service.analyze_conversation(user, analysis_request)
                    
                    await websocket.send_json({
                        "type": "analysis",
                        "feedback_id": str(feedback.id),
                        "conversation_exchanges": feedback.conversation_exchanges,
                        "mistakes": feedback.mistakes,
                        "strengths": feedback.strengths,
                        "suggestions": feedback.suggestions,
                        "improved_sentences": feedback.improved_sentences,
                        "vocabulary_suggestions": feedback.vocabulary_suggestions,
                        "word_bank": feedback.word_bank,
                        "scores": {
                            "overall": feedback.overall_score,
                            "fluency": feedback.fluency_score,
                            "grammar": feedback.grammar_score,
                            "vocabulary": feedback.vocabulary_score,
                            "pronunciation": feedback.pronunciation_score
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to analyze conversation: {e}")
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to analyze conversation"
                        })
                    except:
                        logger.error("Could not send error message - WebSocket already closed")
                # Continue conversation after analysis
                
            elif data["type"] == "end_conversation":
                # Analyze conversation and end it
                language_service = LanguageLearningService()
                from app.schemas.language_learning import ConversationAnalysisRequest
                
                # For end conversation, we typically want to force a new analysis
                analysis_request = ConversationAnalysisRequest(
                    session_id=str(session.id),
                    language=language,
                    force_reanalysis=True
                )
                
                try:
                    feedback = await language_service.analyze_conversation(user, analysis_request)
                    
                    await websocket.send_json({
                        "type": "analysis",
                        "feedback_id": str(feedback.id),
                        "conversation_exchanges": feedback.conversation_exchanges,
                        "mistakes": feedback.mistakes,
                        "strengths": feedback.strengths,
                        "suggestions": feedback.suggestions,
                        "improved_sentences": feedback.improved_sentences,
                        "vocabulary_suggestions": feedback.vocabulary_suggestions,
                        "word_bank": feedback.word_bank,
                        "scores": {
                            "overall": feedback.overall_score,
                            "fluency": feedback.fluency_score,
                            "grammar": feedback.grammar_score,
                            "vocabulary": feedback.vocabulary_score,
                            "pronunciation": feedback.pronunciation_score
                        }
                    })
                except Exception as e:
                    logger.error(f"Failed to analyze conversation: {e}")
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to analyze conversation"
                        })
                    except:
                        logger.error("Could not send error message - WebSocket already closed")
                
                await websocket.close()
                break
            
            else:
                logger.warning(f"Unknown message type: {data.get('type', 'unknown')}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {data.get('type', 'unknown')}"
                    })
                except:
                    logger.error("Could not send error message - WebSocket already closed")
                
    except WebSocketDisconnect:
        manager.disconnect(str(user.id))
        logger.info(f"User {user.id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            logger.error("Could not send error message - WebSocket already closed")
        await websocket.close()