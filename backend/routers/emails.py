from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from db import get_db
from models import User, Email, Thread, AccountToken
from schemas import EmailResponse, EmailSyncRequest
from app.dependencies import get_current_user
from services import EmailSyncService
from services.gmail_service import GmailService
from services.outlook_service import OutlookService
from core import NotFoundError, ExternalServiceError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/sync")
def trigger_email_sync(
    sync_request: EmailSyncRequest,
    provider: Optional[str] = Query(None, description="Specific provider to sync (gmail/outlook)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger manual email sync

    Fetches emails from connected accounts (Gmail/Outlook)
    and stores them in the database.

    Query parameters:
    - provider: Sync specific provider only (gmail or outlook)
    - force: Force full sync instead of incremental

    Returns sync statistics with number of emails and threads synced.
    """
    try:
        sync_service = EmailSyncService(db, current_user)

        # Sync specific provider or all accounts
        if provider == 'gmail':
            stats = sync_service.sync_gmail(full_sync=sync_request.force)
        elif provider == 'outlook':
            stats = sync_service.sync_outlook(full_sync=sync_request.force)
        else:
            stats = sync_service.sync_all_accounts(full_sync=sync_request.force)

        logger.info(f"Email sync completed for user {current_user.email}: {stats}")

        return {
            "success": True,
            "message": "Email sync completed",
            "stats": stats
        }

    except ValueError as e:
        raise NotFoundError(str(e))
    except Exception as e:
        logger.error(f"Email sync failed for user {current_user.email}: {str(e)}")
        raise ExternalServiceError(f"Email sync failed: {str(e)}")


@router.get("/sync/status")
def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get sync status for connected accounts

    Returns last sync time, status, and connected email addresses
    for each provider (Gmail/Outlook).
    """
    sync_service = EmailSyncService(db, current_user)
    status = sync_service.get_sync_status()

    return status


@router.get("/{email_id}", response_model=EmailResponse)
def get_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single email by ID"""
    email = (
        db.query(Email)
        .filter(Email.id == email_id, Email.user_id == current_user.id)
        .first()
    )

    if not email:
        raise NotFoundError("Email not found")

    return email


# Pydantic models for email sending
class SendEmailRequest(BaseModel):
    """Request to send a new email"""
    to: str
    subject: str
    body: str
    provider: str  # 'gmail' or 'outlook'
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    html: bool = False


class SendReplyRequest(BaseModel):
    """Request to send a reply to a thread"""
    thread_id: str
    body: str
    html: bool = False


@router.post("/send")
def send_email(
    request: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a new email via Gmail or Outlook

    Requires:
    - to: Recipient email address
    - subject: Email subject
    - body: Email body (plain text or HTML)
    - provider: 'gmail' or 'outlook'

    Optional:
    - cc: List of CC recipients
    - bcc: List of BCC recipients
    - html: Whether body is HTML (default: False)
    """
    try:
        # Check if user has connected the provider
        account = (
            db.query(AccountToken)
            .filter(
                AccountToken.user_id == current_user.id,
                AccountToken.provider == request.provider
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=400,
                detail=f"{request.provider.capitalize()} account not connected"
            )

        # Send via appropriate service
        if request.provider == 'gmail':
            service = GmailService(db, current_user)
            result = service.send_message(
                to=request.to,
                subject=request.subject,
                body=request.body,
                cc=request.cc,
                bcc=request.bcc,
                html=request.html
            )
        elif request.provider == 'outlook':
            service = OutlookService(db, current_user)
            result = service.send_message(
                to=request.to,
                subject=request.subject,
                body=request.body,
                is_html=request.html,
                cc=request.cc,
                bcc=request.bcc
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")

        logger.info(f"Email sent via {request.provider} to {request.to}")

        return {
            "success": True,
            "message": "Email sent successfully",
            "provider": request.provider,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/reply")
def send_reply(
    request: SendReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a reply to an existing email thread

    Requires:
    - thread_id: Thread ID to reply to
    - body: Reply body (plain text or HTML)

    Optional:
    - html: Whether body is HTML (default: False)

    The service will automatically:
    - Determine the provider (Gmail or Outlook)
    - Find the recipient from the original thread
    - Add proper threading headers
    - Use appropriate subject line (with Re: prefix)
    """
    try:
        # Get the thread
        thread = (
            db.query(Thread)
            .filter(
                Thread.id == request.thread_id,
                Thread.user_id == current_user.id
            )
            .first()
        )

        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Get the latest email to determine provider
        latest_email = (
            db.query(Email)
            .filter(Email.thread_id == thread.id)
            .order_by(Email.received_at.desc())
            .first()
        )

        if not latest_email:
            raise HTTPException(status_code=404, detail="No emails found in thread")

        # Determine provider from the thread's provider ID format
        # Gmail thread IDs are typically hex strings
        # Outlook conversation IDs are longer alphanumeric strings
        provider = None
        if thread.thread_id_provider and len(thread.thread_id_provider) <= 20:
            provider = 'gmail'
        else:
            provider = 'outlook'

        # Verify user has account connected
        account = (
            db.query(AccountToken)
            .filter(
                AccountToken.user_id == current_user.id,
                AccountToken.provider == provider
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=400,
                detail=f"{provider.capitalize()} account not connected"
            )

        # Send reply via appropriate service
        if provider == 'gmail':
            service = GmailService(db, current_user)
            result = service.send_reply(
                thread_id=thread.thread_id_provider,
                body=request.body,
                html=request.html
            )
        else:  # outlook
            service = OutlookService(db, current_user)
            # For Outlook, we need the message ID, not thread ID
            result = service.send_reply(
                message_id=latest_email.email_id_provider,
                body=request.body,
                is_html=request.html
            )

        logger.info(f"Reply sent to thread {request.thread_id} via {provider}")

        return {
            "success": True,
            "message": "Reply sent successfully",
            "provider": provider,
            "thread_id": request.thread_id,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send reply: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")
