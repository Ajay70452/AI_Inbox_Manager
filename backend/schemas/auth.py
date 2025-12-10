from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserSignup(BaseModel):
    """User signup request"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login request"""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request"""

    refresh_token: str


class OAuth2CallbackResponse(BaseModel):
    """OAuth2 callback response"""

    success: bool
    message: str
    provider: str
    email_address: Optional[str] = None
