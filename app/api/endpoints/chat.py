from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSession as ChatSessionSchema,
    ChatMessage as ChatMessageSchema,
    ChatSessionCreate,
    ChatSessionUpdate
)
from app.services.chat import ChatService


router = APIRouter()
chat_service = ChatService()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    try:
        result = await chat_service.send_message(
            user=current_user,
            message=request.message,
            session_id=request.session_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        # Result is already a dictionary with proper string values
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/sessions")
async def create_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    session = await chat_service.create_session(current_user, session_data)
    
    # Manually serialize the session data
    session_data = {
        "id": str(session.id),
        "user_id": str(session.user.id),
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "is_active": session.is_active,
        "metadata": session.metadata
    }
    
    return JSONResponse(content=session_data)


@router.get("/sessions")
async def get_sessions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    sessions = await chat_service.get_user_sessions(str(current_user.id), skip, limit)
    
    # Manually serialize the sessions
    sessions_data = []
    for session in sessions:
        try:
            # Handle case where user might not be populated
            user_id = str(session.user.id) if hasattr(session.user, 'id') else str(session.user)
            session_data = {
                "id": str(session.id),
                "user_id": user_id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "is_active": session.is_active,
                "metadata": session.metadata
            }
            sessions_data.append(session_data)
        except Exception as e:
            print(f"Error serializing session {session.id}: {e}")
            continue
    
    return JSONResponse(content=sessions_data)


@router.get("/sessions/{session_id}", response_model=ChatSessionSchema)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    session = await chat_service.get_session(session_id, str(current_user.id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    session = await chat_service.update_session(session_id, str(current_user.id), update_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Manually serialize the session data
    session_data = {
        "id": str(session.id),
        "user_id": str(session.user.id) if hasattr(session.user, 'id') else str(session.user),
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "is_active": session.is_active,
        "metadata": session.metadata
    }
    
    return JSONResponse(content=session_data)


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    session = await chat_service.get_session(session_id, str(current_user.id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    print(f"Getting messages for session {session_id}")
    messages = await chat_service.get_session_messages(session_id, skip, limit)
    print(f"Found {len(messages)} messages")
    
    # Manually serialize the messages
    messages_data = []
    for message in messages:
        # Handle session reference properly
        session_id_str = str(message.session.id) if hasattr(message.session, 'id') else str(message.session)
        message_data = {
            "id": str(message.id),
            "session_id": session_id_str,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
            "token_count": message.token_count
        }
        messages_data.append(message_data)
        print(f"Message {message.id}: role={message.role}, content_preview={message.content[:50]}...")
    
    return JSONResponse(content=messages_data)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    success = await chat_service.delete_session(session_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or unauthorized")
    return JSONResponse(content={"message": "Session deleted successfully"})


@router.get("/debug/messages/{session_id}")
async def debug_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import JSONResponse
    from beanie import PydanticObjectId
    
    # Check if session exists
    session = await ChatSession.get(session_id)
    if not session:
        return JSONResponse(content={"error": f"Session {session_id} not found"})
    
    # Try different ways to query messages
    print(f"\n=== DEBUG: Checking messages for session {session_id} ===")
    
    # Method 1: Direct query with string ID
    messages1 = await ChatMessage.find(
        ChatMessage.session.id == session_id
    ).to_list()
    print(f"Method 1 (string ID): Found {len(messages1)} messages")
    
    # Method 2: Query with PydanticObjectId
    messages2 = await ChatMessage.find(
        ChatMessage.session.id == PydanticObjectId(session_id)
    ).to_list()
    print(f"Method 2 (PydanticObjectId): Found {len(messages2)} messages")
    
    # Method 3: Query with MongoDB syntax
    messages3 = await ChatMessage.find(
        {"session.$id": PydanticObjectId(session_id)}
    ).to_list()
    print(f"Method 3 (MongoDB syntax): Found {len(messages3)} messages")
    
    # Method 4: Get all messages and filter
    all_messages = await ChatMessage.find_all().to_list()
    print(f"Total messages in database: {len(all_messages)}")
    
    session_messages = []
    for msg in all_messages:
        # Fetch the session link to get actual ID
        await msg.fetch_link(ChatMessage.session)
        
        # Check session reference
        if hasattr(msg.session, 'id'):
            msg_session_id = str(msg.session.id)
        else:
            msg_session_id = str(msg.session)
            
        print(f"Message {msg.id}: session_id={msg_session_id}, matches={msg_session_id == session_id}")
        
        if msg_session_id == session_id:
            session_messages.append({
                "id": str(msg.id),
                "session_id": msg_session_id,
                "role": msg.role,
                "content": msg.content[:50] + "...",
                "timestamp": msg.timestamp.isoformat()
            })
    
    return JSONResponse(content={
        "session_id": session_id,
        "session_exists": True,
        "method1_count": len(messages1),
        "method2_count": len(messages2),
        "method3_count": len(messages3),
        "total_messages": len(all_messages),
        "filtered_messages": len(session_messages),
        "messages": session_messages
    })