"""
Webhook Handlers

Handles incoming webhooks from Gmail and Outlook for real-time email notifications
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging
import json
import base64
import hmac
import hashlib

from db import get_db
from models import User, AccountToken
from services.gmail_service import GmailService
from services.outlook_service import OutlookService
from workers.redis_client import RedisClient
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
redis_client = RedisClient()


@router.post("/gmail/push")
async def gmail_push_notification(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Gmail push notifications

    Gmail sends notifications when new emails arrive via Cloud Pub/Sub.
    This endpoint processes those notifications and triggers email sync.

    Reference: https://developers.google.com/gmail/api/guides/push
    """
    try:
        # Parse Pub/Sub message
        body = await request.json()

        if not body.get('message'):
            logger.warning("Received Gmail webhook without message")
            return {"status": "ignored"}

        message = body['message']

        # Decode the data
        if 'data' in message:
            data = base64.b64decode(message['data']).decode('utf-8')
            notification_data = json.loads(data) if data else {}
        else:
            notification_data = {}

        # Extract email address from attributes
        email_address = message.get('attributes', {}).get('emailAddress')
        history_id = notification_data.get('historyId')

        logger.info(f"Gmail push notification received for {email_address}, historyId: {history_id}")

        if not email_address:
            logger.warning("No email address in Gmail push notification")
            return {"status": "ignored"}

        # Find user by Gmail account
        account = (
            db.query(AccountToken)
            .filter(
                AccountToken.provider == 'gmail',
                AccountToken.email == email_address
            )
            .first()
        )

        if not account:
            logger.warning(f"No account found for Gmail address: {email_address}")
            return {"status": "ignored"}

        # Enqueue email sync job
        job_data = {
            'user_id': str(account.user_id),
            'provider': 'gmail',
            'history_id': history_id,
            'incremental': True
        }

        redis_client.enqueue('email_sync', job_data)
        logger.info(f"Enqueued Gmail sync job for user {account.user_id}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Gmail webhook: {str(e)}")
        # Return 200 to prevent Gmail from retrying
        return {"status": "error", "message": str(e)}


@router.post("/outlook/push")
async def outlook_push_notification(
    request: Request,
    db: Session = Depends(get_db),
    validation_token: Optional[str] = None
):
    """
    Handle Outlook push notifications

    Microsoft Graph sends notifications when subscriptions are created (validation)
    and when new emails arrive.

    Reference: https://docs.microsoft.com/en-us/graph/webhooks
    """
    try:
        # Handle subscription validation
        if validation_token:
            logger.info("Outlook webhook validation received")
            # Return the validation token as plain text
            return validation_token

        # Parse notification
        body = await request.json()

        if not body.get('value'):
            logger.warning("Received Outlook webhook without value")
            return {"status": "ignored"}

        notifications = body['value']

        for notification in notifications:
            change_type = notification.get('changeType')
            resource = notification.get('resource')
            client_state = notification.get('clientState')

            logger.info(f"Outlook notification: changeType={change_type}, resource={resource}")

            # Verify client state (security check)
            if client_state != settings.OUTLOOK_WEBHOOK_CLIENT_STATE:
                logger.warning(f"Invalid client state in Outlook webhook: {client_state}")
                continue

            # Extract user email from resource
            # Resource format: "Users/{user_id}/Messages/{message_id}"
            # We need to find the account by subscription ID stored in our DB
            subscription_id = notification.get('subscriptionId')

            if not subscription_id:
                logger.warning("No subscription ID in Outlook notification")
                continue

            # Find account by subscription ID (stored in AccountToken metadata)
            account = (
                db.query(AccountToken)
                .filter(
                    AccountToken.provider == 'outlook',
                    AccountToken.metadata.contains({'subscription_id': subscription_id})
                )
                .first()
            )

            if not account:
                logger.warning(f"No account found for Outlook subscription: {subscription_id}")
                continue

            # Enqueue email sync job
            job_data = {
                'user_id': str(account.user_id),
                'provider': 'outlook',
                'change_type': change_type,
                'resource': resource,
                'incremental': True
            }

            redis_client.enqueue('email_sync', job_data)
            logger.info(f"Enqueued Outlook sync job for user {account.user_id}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Outlook webhook: {str(e)}")
        # Return 200 to prevent Outlook from retrying
        return {"status": "error", "message": str(e)}


@router.get("/outlook/push")
async def outlook_webhook_validation(
    validationToken: Optional[str] = None
):
    """
    Handle Outlook webhook validation (GET request)

    When creating a subscription, Microsoft sends a GET request with validationToken.
    We must respond with the token in plain text.
    """
    if validationToken:
        logger.info(f"Outlook webhook validation: {validationToken}")
        return validationToken

    raise HTTPException(status_code=400, detail="No validation token provided")


@router.post("/gmail/watch")
async def setup_gmail_watch(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Setup Gmail push notifications for a user

    This endpoint sets up a watch on the user's Gmail inbox to receive
    push notifications when new emails arrive.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Setup Gmail watch
        gmail_service = GmailService(db, user)
        watch_response = gmail_service.setup_push_notifications()

        logger.info(f"Gmail watch setup for user {user_id}: {watch_response}")

        return {
            "success": True,
            "message": "Gmail push notifications enabled",
            "watch": watch_response
        }

    except Exception as e:
        logger.error(f"Failed to setup Gmail watch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outlook/subscription")
async def setup_outlook_subscription(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Setup Outlook webhook subscription for a user

    This endpoint creates a webhook subscription for the user's Outlook inbox
    to receive push notifications when new emails arrive.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Setup Outlook subscription
        outlook_service = OutlookService(db, user)
        subscription = outlook_service.setup_webhook_subscription()

        logger.info(f"Outlook subscription setup for user {user_id}: {subscription}")

        return {
            "success": True,
            "message": "Outlook webhook subscription created",
            "subscription": subscription
        }

    except Exception as e:
        logger.error(f"Failed to setup Outlook subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
