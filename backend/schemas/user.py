from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """User creation schema"""

    password: str


class UserUpdate(BaseModel):
    """User update schema"""

    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserPasswordUpdate(BaseModel):
    """Password update schema"""

    old_password: str
    new_password: str


class UserResponse(UserBase):
    """User response schema"""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
