from datetime import datetime, timezone
from typing import Optional, List
from beanie import Document, Indexed, Link
from pydantic import EmailStr, Field


class Permission(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    resource: str
    action: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "permissions"


class Role(Document):
    name: Indexed(str, unique=True)
    description: Optional[str] = None
    permissions: List[Link[Permission]] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "roles"


class User(Document):
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    roles: List[Link[Role]] = []
    preferred_language: Optional[str] = "en"  # Language code
    learning_languages: List[str] = []  # List of language codes
    profile_picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "users"