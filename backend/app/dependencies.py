from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from db import get_db
from models import User
from core import decode_token, AuthenticationError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token

    Usage:
    @router.get("/")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"user_id": current_user.id}
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise AuthenticationError("Invalid token")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthenticationError("User not found")

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication dependency
    Returns User if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
