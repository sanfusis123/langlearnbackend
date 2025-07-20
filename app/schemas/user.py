from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    pass


class Permission(PermissionBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[str] = []


class Role(RoleBase):
    id: str
    permissions: List[Permission] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    preferred_language: Optional[str] = "en"
    learning_languages: List[str] = []
    profile_picture: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_ids: List[str] = []


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_ids: Optional[List[str]] = None
    preferred_language: Optional[str] = None
    learning_languages: Optional[List[str]] = None
    profile_picture: Optional[str] = None


class UserInDB(UserBase):
    id: str
    hashed_password: str
    roles: List[Role] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserBase):
    id: str
    roles: List[Role] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None