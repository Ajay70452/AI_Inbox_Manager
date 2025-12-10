from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from models import User, CompanyContext
from schemas import CompanyContextCreate, CompanyContextUpdate, CompanyContextResponse
from app.dependencies import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=CompanyContextResponse)
def get_company_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get company context for current user"""
    context = (
        db.query(CompanyContext)
        .filter(CompanyContext.user_id == current_user.id)
        .first()
    )

    if not context:
        # Create empty context if doesn't exist
        context = CompanyContext(user_id=current_user.id)
        db.add(context)
        db.commit()
        db.refresh(context)

    return context


@router.put("/", response_model=CompanyContextResponse)
def update_company_context(
    context_data: CompanyContextUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update company context"""
    context = (
        db.query(CompanyContext)
        .filter(CompanyContext.user_id == current_user.id)
        .first()
    )

    if not context:
        # Create new context
        context = CompanyContext(user_id=current_user.id)
        db.add(context)

    # Update fields
    if context_data.tone is not None:
        context.tone = context_data.tone
    if context_data.company_description is not None:
        context.company_description = context_data.company_description
    if context_data.products is not None:
        context.products = context_data.products
    if context_data.policies is not None:
        context.policies = context_data.policies
    if context_data.faq is not None:
        context.faq = context_data.faq
    if context_data.roles is not None:
        context.roles = context_data.roles

    db.commit()
    db.refresh(context)

    logger.info(f"Company context updated for user: {current_user.email}")
    return context


@router.delete("/{section}")
def delete_context_section(
    section: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a specific section of company context"""
    context = (
        db.query(CompanyContext)
        .filter(CompanyContext.user_id == current_user.id)
        .first()
    )

    if not context:
        return {"error": "Context not found"}

    # Clear specific section
    if hasattr(context, section):
        setattr(context, section, None)
        db.commit()
        return {"message": f"Section '{section}' cleared"}

    return {"error": f"Section '{section}' not found"}
