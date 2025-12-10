from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import User
from schemas import UserResponse, UserUpdate, UserPasswordUpdate
from app.dependencies import get_current_user
from core import verify_password, get_password_hash, AuthenticationError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile"""
    if user_data.name is not None:
        current_user.name = user_data.name

    if user_data.email is not None:
        # Check if email is already taken
        existing_user = (
            db.query(User)
            .filter(User.email == user_data.email, User.id != current_user.id)
            .first()
        )
        if existing_user:
            raise AuthenticationError("Email already in use")
        current_user.email = user_data.email

    db.commit()
    db.refresh(current_user)

    logger.info(f"User profile updated: {current_user.email}")
    return current_user


@router.put("/password")
def update_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user password"""
    # Verify old password
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise AuthenticationError("Invalid current password")

    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    logger.info(f"Password updated for user: {current_user.email}")
    return {"message": "Password updated successfully"}


@router.delete("/")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user account"""
    db.delete(current_user)
    db.commit()

    logger.info(f"User account deleted: {current_user.email}")
    return {"message": "Account deleted successfully"}
