from typing import Optional, List
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    @staticmethod
    async def create_user(user_create: UserCreate) -> User:
        user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=get_password_hash(user_create.password),
            is_active=user_create.is_active,
            is_superuser=user_create.is_superuser,
        )
        
        if user_create.role_ids:
            roles = await Role.find({"_id": {"$in": user_create.role_ids}}).to_list()
            user.roles = roles
        
        await user.insert()
        return user
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[User]:
        return await User.find_one(User.username == username)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        return await User.find_one(User.email == email)
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[User]:
        return await User.get(user_id)
    
    @staticmethod
    async def update_user(user_id: str, user_update: UserUpdate) -> Optional[User]:
        user = await User.get(user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        if "role_ids" in update_data:
            role_ids = update_data.pop("role_ids")
            if role_ids is not None:
                roles = await Role.find({"_id": {"$in": role_ids}}).to_list()
                user.roles = roles
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await user.save()
        return user
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        user = await User.get(user_id)
        if not user:
            return False
        await user.delete()
        return True
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        user = await UserService.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    async def get_all_users(skip: int = 0, limit: int = 100) -> List[User]:
        return await User.find_all().skip(skip).limit(limit).to_list()