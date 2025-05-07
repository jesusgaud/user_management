
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, HttpUrl, root_validator
from app.models.user_model import UserRole

class UserBase(BaseModel):
    email: EmailStr
    nickname: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None
    linkedin_profile_url: Optional[HttpUrl] = None
    github_profile_url: Optional[HttpUrl] = None
    is_professional: Optional[bool] = None
    role: Optional[UserRole] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None
    linkedin_profile_url: Optional[HttpUrl] = None
    github_profile_url: Optional[HttpUrl] = None
    role: Optional[UserRole] = None

    @root_validator(pre=True)
    def check_at_least_one_value(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values

class UserResponse(UserBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    links: Optional[dict] = None

class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    links: Optional[dict]
