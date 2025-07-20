from typing import Optional, List
from datetime import datetime, timezone
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.models.token_usage import TokenUsage
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate
from app.llm.agents.chat_agent import ChatAgent
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.chat_agent = ChatAgent()
    
    @staticmethod
    async def create_session(user: User, session_data: ChatSessionCreate) -> ChatSession:
        session = ChatSession(
            user=user,
            title=session_data.title or f"Chat {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            metadata=session_data.metadata if hasattr(session_data, 'metadata') else {}
        )
        await session.insert()
        # Fetch links to ensure user is populated
        await session.fetch_link(ChatSession.user)
        
        # Log session creation with scenario details
        logger.info(f"Created session {session.id} for user {user.id}")
        logger.info(f"Session title: {session.title}")
        logger.info(f"Session metadata: {session.metadata}")
        
        if session.metadata and 'scenario' in session.metadata:
            scenario = session.metadata['scenario']
            logger.info(f"=== SCENARIO DETECTED IN NEW SESSION ===")
            logger.info(f"Scenario ID: {scenario.get('id', 'N/A')}")
            logger.info(f"Scenario Type: {scenario.get('type', 'N/A')}")
            logger.info(f"Scenario Title: {scenario.get('title', 'N/A')}")
            logger.info(f"Scenario Description: {scenario.get('description', 'N/A')}")
            logger.info(f"Scenario Role: {scenario.get('role', 'N/A')}")
            logger.info(f"======================================")
        else:
            logger.info("No scenario attached to this session")
            
        return session
    
    @staticmethod
    async def get_session(session_id: str, user_id: str) -> Optional[ChatSession]:
        session = await ChatSession.get(session_id)
        if session:
            await session.fetch_link(ChatSession.user)
            if str(session.user.id) == user_id:
                return session
        return None
    
    @staticmethod
    async def get_user_sessions(user_id: str, skip: int = 0, limit: int = 50) -> List[ChatSession]:
        from beanie import PydanticObjectId
        # Try different query approaches
        sessions = await ChatSession.find(
            ChatSession.user.id == PydanticObjectId(user_id),
            ChatSession.is_active == True
        ).skip(skip).limit(limit).sort(-ChatSession.updated_at).to_list()
        
        # Fetch links for each session
        for session in sessions:
            await session.fetch_link(ChatSession.user)
        
        # Log for debugging
        print(f"Fetching sessions for user_id: {user_id}")
        print(f"Found {len(sessions)} sessions")
        for session in sessions:
            print(f"Session {session.id}: {session.title}, User: {session.user.id if hasattr(session.user, 'id') else 'No user'}")
        
        return sessions
    
    @staticmethod
    async def update_session(session_id: str, user_id: str, update_data: ChatSessionUpdate) -> Optional[ChatSession]:
        session = await ChatService.get_session(session_id, user_id)
        if not session:
            return None
        
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(session, field, value)
        
        session.updated_at = datetime.now(timezone.utc)
        await session.save()
        # Ensure user link is fetched
        await session.fetch_link(ChatSession.user)
        return session
    
    @staticmethod
    async def get_session_messages(session_id: str, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        from beanie import PydanticObjectId
        
        # First get the session document
        session = await ChatSession.get(session_id)
        if not session:
            print(f"Session {session_id} not found")
            return []
        
        # Query messages using the session document reference
        messages = await ChatMessage.find(
            ChatMessage.session.id == session.id
        ).skip(skip).limit(limit).sort(ChatMessage.timestamp).to_list()
        
        # If no messages found, try alternative query method
        if len(messages) == 0:
            print(f"No messages found with first method, trying alternative...")
            # Try finding with the session document itself
            messages = await ChatMessage.find(
                {"session.$id": PydanticObjectId(session_id)}
            ).skip(skip).limit(limit).sort(ChatMessage.timestamp).to_list()
        
        # Fetch session links for each message
        for message in messages:
            await message.fetch_link(ChatMessage.session)
        
        print(f"Found {len(messages)} messages for session {session_id}")
        return messages
    
    def _create_scenario_system_prompt(self, scenario_metadata: dict, language: str) -> str:
        """Create a system prompt based on the scenario metadata"""
        logger.info(f"=== CREATING SCENARIO SYSTEM PROMPT ===")
        logger.info(f"Scenario metadata: {scenario_metadata}")
        logger.info(f"Language: {language}")
        
        if not scenario_metadata:
            logger.info("No scenario metadata provided, returning None")
            return None
            
        scenario_type = scenario_metadata.get('type', 'free')
        logger.info(f"Scenario type: {scenario_type}")
        
        if scenario_type == 'predefined':
            # Predefined scenarios like job interview, restaurant, etc.
            scenario_id = scenario_metadata.get('id', '')
            scenario_title = scenario_metadata.get('title', '')
            scenario_description = scenario_metadata.get('description', '')
            
            prompts = {
                'job_interview': f"""You are conducting a job interview in {language}. You are a professional HR manager or hiring manager. 
                
Your role:
- Ask relevant interview questions about experience, skills, and career goals
- Respond naturally to the candidate's answers
- Follow up with probing questions
- Maintain a professional but friendly tone
- Occasionally ask for clarification or examples
- Adapt your questions based on their responses
- Speak ONLY in {language}

Start by greeting the candidate and asking them to tell you about themselves.""",
                
                'restaurant': f"""You are a waiter/waitress at a restaurant, speaking only in {language}.

Your role:
- Greet customers warmly
- Present the menu and daily specials
- Take orders and answer questions about dishes
- Suggest drinks and desserts
- Handle special requests or dietary restrictions
- Be helpful and attentive
- Speak ONLY in {language}

Start by greeting the customer and asking if they would like to see the menu.""",
                
                'business_meeting': f"""You are a colleague in a business meeting, speaking only in {language}.

Your role:
- Discuss project updates and deadlines
- Ask for status reports and clarifications
- Propose solutions to problems
- Schedule follow-up actions
- Maintain professional language
- Encourage participation
- Speak ONLY in {language}

Start by welcoming everyone to the meeting and asking for project updates.""",
                
                'travel': f"""You are a travel agent or hotel receptionist, speaking only in {language}.

Your role:
- Help with travel bookings and recommendations
- Provide information about destinations
- Assist with hotel check-in/check-out
- Give directions and local tips
- Handle travel-related problems
- Be informative and helpful
- Speak ONLY in {language}

Start by greeting the traveler and asking how you can help them today.""",
                
                'shopping': f"""You are a shop assistant in a clothing store, speaking only in {language}.

Your role:
- Greet customers and offer assistance
- Help find sizes and styles
- Suggest items and give opinions
- Explain prices and discounts
- Handle payment questions
- Be friendly and helpful
- Speak ONLY in {language}

Start by greeting the customer and asking if they need any help.""",
                
                'doctor_visit': f"""You are a doctor in a medical consultation, speaking only in {language}.

Your role:
- Ask about symptoms and medical history
- Show empathy and understanding
- Explain diagnoses in simple terms
- Give medical advice and prescriptions
- Answer health-related questions
- Maintain professional medical manner
- Speak ONLY in {language}

Start by greeting the patient and asking what brings them in today."""
            }
            
            selected_prompt = prompts.get(scenario_id, f"You are helping someone practice {language} in a {scenario_title} scenario. {scenario_description}. Speak ONLY in {language}.")
            logger.info(f"Selected predefined prompt for scenario '{scenario_id}'")
            logger.info(f"Prompt preview: {selected_prompt[:200]}...")
            return selected_prompt
            
        elif scenario_type == 'meeting':
            # Meeting-based scenarios from past analyses
            meeting_name = scenario_metadata.get('title', 'Business Meeting')
            meeting_prompt = f"""You are a colleague in a meeting similar to '{meeting_name}', speaking only in {language}.

Your role:
- Ask questions that would naturally come up in such meetings
- Respond to updates and information shared
- Request clarifications when needed
- Maintain the professional context
- Speak ONLY in {language}

Start by setting the meeting context and asking for an update."""
            logger.info(f"Created meeting scenario prompt for '{meeting_name}'")
            logger.info(f"Prompt preview: {meeting_prompt[:200]}...")
            return meeting_prompt
            
        elif scenario_type == 'custom':
            # Custom AI-generated scenarios
            title = scenario_metadata.get('title', '')
            description = scenario_metadata.get('description', '')
            role = scenario_metadata.get('role', 'conversation partner')
            
            custom_prompt = f"""You are playing the role of {role} in the following scenario:
Title: {title}
Context: {description}

Your role:
- Stay in character throughout the conversation
- Create realistic dialogue for this scenario
- Ask relevant questions and respond naturally
- Adapt to the user's responses
- Maintain appropriate tone for the scenario
- Speak ONLY in {language}

Start the conversation in a way that fits this scenario."""
            logger.info(f"Created custom scenario prompt")
            logger.info(f"Title: {title}")
            logger.info(f"Role: {role}")
            logger.info(f"Description: {description}")
            logger.info(f"Prompt preview: {custom_prompt[:200]}...")
            return custom_prompt
            
        else:
            # Free conversation
            logger.info(f"Unknown scenario type '{scenario_type}' or free conversation, returning None")
            return None
    
    async def send_message(
        self,
        user: User,
        message: str,
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        if session_id:
            session = await self.get_session(session_id, str(user.id))
            if not session:
                raise ValueError("Session not found or unauthorized")
        else:
            session = await self.create_session(user, ChatSessionCreate())
        
        # Get conversation history
        chat_history = await self.get_session_messages(str(session.id))
        history_dicts = []
        
        logger.info(f"=== SEND MESSAGE - SESSION {session.id} ===")
        logger.info(f"Message from user: {message[:100]}...")
        logger.info(f"Session has {len(chat_history)} existing messages")
        logger.info(f"Session metadata: {session.metadata}")
        
        # Check if this is the start of a scenario-based conversation
        scenario_metadata = session.metadata.get('scenario', {})
        if scenario_metadata and len(chat_history) == 0:
            logger.info("=== SCENARIO ACTIVATION ===")
            logger.info("This is the FIRST message in a scenario-based conversation")
            logger.info(f"Scenario details: {scenario_metadata}")
            
            # This is the first message in a scenario-based conversation
            language = session.metadata.get('language', 'English')
            logger.info(f"Language for scenario: {language}")
            
            system_prompt = self._create_scenario_system_prompt(scenario_metadata, language)
            
            if system_prompt:
                logger.info("System prompt created successfully")
                logger.info(f"System prompt length: {len(system_prompt)} characters")
                # Add system message to guide the AI's behavior
                history_dicts.append({
                    "role": "system",
                    "content": system_prompt
                })
                logger.info("System prompt added to conversation history")
            else:
                logger.warning("No system prompt was created for this scenario")
        else:
            if scenario_metadata:
                logger.info(f"Scenario exists but conversation already started ({len(chat_history)} messages)")
            else:
                logger.info("No scenario attached to this session")
        
        # Add existing messages to history
        for msg in chat_history:
            history_dicts.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Save user message
        user_message = ChatMessage(
            session=session,
            role="user",
            content=message,
            token_count=self.chat_agent.llm_provider.count_tokens(message)
        )
        await user_message.insert()
        
        # Generate AI response
        result = await self.chat_agent.chat(
            user_input=message,
            chat_history=history_dicts,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Save assistant message
        assistant_message = ChatMessage(
            session=session,
            role="assistant",
            content=result["response"],
            token_count=result["usage"]["completion_tokens"],
            metadata={"model": result["model"]}
        )
        await assistant_message.insert()
        
        # Track token usage
        token_usage = TokenUsage(
            user=user,
            session=session,
            model=result["model"],
            prompt_tokens=result["usage"]["prompt_tokens"],
            completion_tokens=result["usage"]["completion_tokens"],
            total_tokens=result["usage"]["total_tokens"]
        )
        await token_usage.insert()
        
        # Update session timestamp
        session.updated_at = datetime.now(timezone.utc)
        await session.save()
        
        return {
            "response": result["response"],
            "session_id": str(session.id),
            "usage": result["usage"],
            "model": result["model"]
        }
    
    @staticmethod
    async def delete_session(session_id: str, user_id: str) -> bool:
        from beanie import PydanticObjectId
        session = await ChatSession.find_one(
            ChatSession.id == PydanticObjectId(session_id)
        )
        if session:
            await session.fetch_link(ChatSession.user)
            if str(session.user.id) == user_id:
                # Delete all messages first
                await ChatMessage.find(
                    ChatMessage.session.id == PydanticObjectId(session_id)
                ).delete()
                # Then delete the session
                await session.delete()
                return True
        return False