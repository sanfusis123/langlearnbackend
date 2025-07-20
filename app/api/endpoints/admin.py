from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.chat import ChatSession
from app.models.token_usage import TokenUsage
from app.models.language_learning import Language
from app.schemas.user import UserUpdate
from beanie import PydanticObjectId
from datetime import datetime, timezone, timedelta

router = APIRouter()

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to check if user is admin"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.get("/users")
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(get_admin_user)
):
    """Get all users with optional search"""
    query = {}
    if search:
        query = {
            "$or": [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}}
            ]
        }
    
    users = await User.find(query).skip(skip).limit(limit).to_list()
    total = await User.find(query).count()
    
    return JSONResponse(content={
        "users": [
            {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "role": "admin" if user.is_superuser else "user",
                "permissions": [],  # Permissions are managed through roles
                "native_language": user.preferred_language,
                "learning_languages": user.learning_languages,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            for user in users
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    })

@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin: User = Depends(get_admin_user)
):
    """Get detailed information about a specific user"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's session count
    session_count = await ChatSession.find(ChatSession.user.id == user.id).count()
    
    # Get user's token usage summary
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    token_usage = await TokenUsage.find(
        TokenUsage.user.id == user.id,
        TokenUsage.timestamp >= thirty_days_ago
    ).to_list()
    
    total_tokens = sum(usage.total_tokens for usage in token_usage)
    
    return JSONResponse(content={
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "role": "admin" if user.is_superuser else "user",
        "permissions": [],  # Permissions are managed through roles
        "native_language": user.preferred_language,
        "learning_languages": user.learning_languages,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "stats": {
            "session_count": session_count,
            "total_tokens_30d": total_tokens,
            "token_usage_count": len(token_usage)
        }
    })

@router.put("/users/{user_id}")
async def update_user_admin(
    user_id: str,
    user_update: dict,
    admin: User = Depends(get_admin_user)
):
    """Update user information as admin"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update allowed fields
    allowed_fields = [
        "is_active", "is_superuser", "full_name", 
        "preferred_language", "learning_languages"
    ]
    
    for field, value in user_update.items():
        if field in allowed_fields:
            setattr(user, field, value)
        elif field == "role":
            # Handle role separately
            if value == "admin":
                user.is_superuser = True
            else:
                user.is_superuser = False
    
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return JSONResponse(content={"message": "User updated successfully"})

@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    admin: User = Depends(get_admin_user)
):
    """Toggle user active status"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating yourself
    if str(user.id) == str(admin.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = not user.is_active
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return JSONResponse(content={
        "message": f"User {'activated' if user.is_active else 'deactivated'} successfully",
        "is_active": user.is_active
    })

@router.post("/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    user_id: str,
    admin: User = Depends(get_admin_user)
):
    """Toggle user admin status"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent removing your own admin status
    if str(user.id) == str(admin.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot remove your own admin status"
        )
    
    user.is_superuser = not user.is_superuser
    
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return JSONResponse(content={
        "message": f"User {'promoted to' if user.is_superuser else 'removed from'} admin successfully",
        "is_superuser": user.is_superuser,
        "role": "admin" if user.is_superuser else "user"
    })

@router.post("/users/{user_id}/add-permission")
async def add_user_permission(
    user_id: str,
    permission: dict,
    admin: User = Depends(get_admin_user)
):
    """Add a permission to user"""
    # Note: This is a placeholder since permissions are managed through roles
    # In a real implementation, you would modify user roles or create custom permissions
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return JSONResponse(content={
        "message": "Permission system is managed through roles",
        "permissions": []
    })

@router.post("/users/{user_id}/remove-permission")
async def remove_user_permission(
    user_id: str,
    permission: dict,
    admin: User = Depends(get_admin_user)
):
    """Remove a permission from user"""
    # Note: This is a placeholder since permissions are managed through roles
    # In a real implementation, you would modify user roles or create custom permissions
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return JSONResponse(content={
        "message": "Permission system is managed through roles",
        "permissions": []
    })

@router.get("/stats/overview")
async def get_admin_stats(admin: User = Depends(get_admin_user)):
    """Get overall platform statistics"""
    # User stats
    total_users = await User.count()
    active_users = await User.find(User.is_active == True).count()
    admin_users = await User.find(User.is_superuser == True).count()
    
    # Session stats
    total_sessions = await ChatSession.count()
    
    # Token usage stats (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_usage = await TokenUsage.find(
        TokenUsage.timestamp >= thirty_days_ago
    ).to_list()
    
    total_tokens_30d = sum(usage.total_tokens for usage in recent_usage)
    
    # Language stats
    language_stats = {}
    all_users = await User.find_all().to_list()
    for user in all_users:
        for lang in user.learning_languages:
            language_stats[lang] = language_stats.get(lang, 0) + 1
    
    return JSONResponse(content={
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users,
            "inactive": total_users - active_users
        },
        "sessions": {
            "total": total_sessions
        },
        "tokens": {
            "total_last_30_days": total_tokens_30d,
            "usage_count_30d": len(recent_usage)
        },
        "languages": language_stats
    })

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(get_admin_user)
):
    """Delete a user (soft delete by deactivating)"""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if str(user.id) == str(admin.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    # Soft delete by deactivating
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    await user.save()
    
    return JSONResponse(content={"message": "User deactivated successfully"})


# Language Management Endpoints
@router.get("/languages")
async def get_all_languages(admin: User = Depends(get_admin_user)):
    """Get all languages"""
    languages = await Language.find_all().to_list()
    return JSONResponse(content=[
        {
            "id": str(lang.id),
            "code": lang.code,
            "name": lang.name,
            "native_name": lang.native_name,
            "created_at": lang.created_at.isoformat() if hasattr(lang, 'created_at') and lang.created_at else None
        }
        for lang in languages
    ])


@router.post("/languages")
async def create_language(
    language_data: dict,
    admin: User = Depends(get_admin_user)
):
    """Create a new language"""
    # Check if language code already exists
    existing = await Language.find_one(Language.code == language_data.get("code"))
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Language code already exists"
        )
    
    # Validate required fields
    required_fields = ["code", "name", "native_name"]
    for field in required_fields:
        if field not in language_data or not language_data[field]:
            raise HTTPException(
                status_code=400,
                detail=f"Field '{field}' is required"
            )
    
    # Create language
    language = Language(
        code=language_data["code"],
        name=language_data["name"],
        native_name=language_data["native_name"]
    )
    await language.insert()
    
    return JSONResponse(content={
        "id": str(language.id),
        "code": language.code,
        "name": language.name,
        "native_name": language.native_name,
        "message": "Language created successfully"
    })


@router.put("/languages/{language_id}")
async def update_language(
    language_id: str,
    language_data: dict,
    admin: User = Depends(get_admin_user)
):
    """Update a language"""
    language = await Language.get(language_id)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Check if new code conflicts with existing languages
    if "code" in language_data and language_data["code"] != language.code:
        existing = await Language.find_one(Language.code == language_data["code"])
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Language code already exists"
            )
    
    # Update fields
    allowed_fields = ["code", "name", "native_name"]
    for field in allowed_fields:
        if field in language_data:
            setattr(language, field, language_data[field])
    
    await language.save()
    
    return JSONResponse(content={
        "id": str(language.id),
        "code": language.code,
        "name": language.name,
        "native_name": language.native_name,
        "message": "Language updated successfully"
    })


@router.delete("/languages/{language_id}")
async def delete_language(
    language_id: str,
    admin: User = Depends(get_admin_user)
):
    """Delete a language"""
    language = await Language.get(language_id)
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    
    # Check if language is being used by users
    users_using_language = await User.find(
        {"$or": [
            {"preferred_language": language.code},
            {"learning_languages": language.code}
        ]}
    ).to_list()
    
    if users_using_language:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete language. {len(users_using_language)} users are using this language."
        )
    
    await language.delete()
    
    return JSONResponse(content={"message": "Language deleted successfully"})