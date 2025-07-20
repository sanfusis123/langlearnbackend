from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_active_user, get_current_active_superuser, check_permission
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.services.user import UserService


router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate
):
    """Public endpoint for user registration"""
    from fastapi.responses import JSONResponse
    
    existing_user = await UserService.get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    existing_user = await UserService.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    user = await UserService.create_user(user_in)
    
    # Manually serialize the user data
    user_data = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "preferred_language": user.preferred_language,
        "learning_languages": user.learning_languages,
        "profile_picture": user.profile_picture,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "roles": []
    }
    
    return JSONResponse(content=user_data, status_code=status.HTTP_201_CREATED)


@router.post("/admin", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_in: UserCreate,
    current_user: User = Depends(check_permission("users", "create"))
):
    """Admin endpoint for creating users with role assignment"""
    existing_user = await UserService.get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    existing_user = await UserService.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    user = await UserService.create_user(user_in)
    return user


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # Manually serialize the user data
    from fastapi.responses import JSONResponse
    
    user_data = {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "preferred_language": current_user.preferred_language,
        "learning_languages": current_user.learning_languages,
        "profile_picture": current_user.profile_picture,
        "created_at": current_user.created_at.isoformat(),
        "updated_at": current_user.updated_at.isoformat(),
        "roles": []
    }
    
    # Handle roles if they exist
    if hasattr(current_user, 'roles') and current_user.roles:
        for role in current_user.roles:
            role_data = {
                "id": str(role.id) if hasattr(role, 'id') else None,
                "name": role.name if hasattr(role, 'name') else None,
                "description": role.description if hasattr(role, 'description') else None,
                "permissions": [],
                "created_at": role.created_at.isoformat() if hasattr(role, 'created_at') else None
            }
            user_data["roles"].append(role_data)
    
    return JSONResponse(content=user_data)


@router.get("/")
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_permission("users", "read"))
):
    from fastapi.responses import JSONResponse
    users = await UserService.get_all_users(skip, limit)
    
    # Manually serialize the users
    users_data = []
    for user in users:
        user_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "preferred_language": user.preferred_language,
            "learning_languages": user.learning_languages,
            "profile_picture": user.profile_picture,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "roles": []
        }
        users_data.append(user_data)
    
    return JSONResponse(content=users_data)


@router.get("/{user_id}", response_model=UserSchema)
async def read_user_by_id(
    user_id: str,
    current_user: User = Depends(check_permission("users", "read"))
):
    user = await UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(check_permission("users", "update"))
):
    from fastapi.responses import JSONResponse
    
    user = await UserService.update_user(user_id, user_in)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Manually serialize the user data
    user_data = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "preferred_language": user.preferred_language,
        "learning_languages": user.learning_languages,
        "profile_picture": user.profile_picture,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "roles": []
    }
    
    return JSONResponse(content=user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(check_permission("users", "delete"))
):
    success = await UserService.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )