"""
Outlook Service

Handles fetching and syncing emails from Microsoft Graph API
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import requests

from models import User, AccountToken, Thread, Email, SyncJobLog
from services.outlook_oauth import OutlookOAuthService
from utils import email_parser, storage_service
from app.config import settings

logger = logging.getLogger(__name__)

GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'


class OutlookService:
    """Service for Outlook email operations"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.oauth_service = OutlookOAuthService()
        self.account_token = self._get_account_token()

    def _get_account_token(self) -> Optional[AccountToken]:
        """Get user's Outlook account token"""
        return (
            self.db.query(AccountToken)
            .filter(
                AccountToken.user_id == self.user.id,
                AccountToken.provider == 'outlook'
            )
            .first()
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated headers for Microsoft Graph API"""
        if not self.account_token:
            raise ValueError("Outlook account not connected")

        access_token = self.oauth_service.get_valid_access_token(
            self.db,
            self.account_token
        )

        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

    def fetch_messages(
        self,
        max_results: int = 100,
        skip: int = 0,
        filter_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch messages from Outlook

        Args:
            max_results: Maximum messages to fetch
            skip: Number of messages to skip (pagination)
            filter_query: OData filter query

        Returns:
            Dictionary with messages and pagination info
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/me/messages"

            params = {
                '$top': min(max_results, 999),
                '$skip': skip,
                '$orderby': 'receivedDateTime DESC'
            }

            if filter_query:
                params['$filter'] = filter_query

            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()

            data = response.json()
            messages = data.get('value', [])

            logger.info(f"Fetched {len(messages)} messages from Outlook")

            return {
                'messages': messages,
                '@odata.nextLink': data.get('@odata.nextLink')
            }

        except Exception as e:
            logger.error(f"Failed to fetch Outlook messages: {str(e)}")
            raise

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get full message details from Outlook

        Args:
            message_id: Outlook message ID

        Returns:
            Full message data
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/me/messages/{message_id}"

            response = requests.get(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get Outlook message {message_id}: {str(e)}")
            raise

    def sync_emails(
        self,
        lookback_days: Optional[int] = None,
        full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync emails from Outlook to database

        Args:
            lookback_days: Days to look back (default from settings)
            full_sync: If True, perform full sync; otherwise incremental

        Returns:
            Sync statistics
        """
        start_time = datetime.utcnow()
        stats = {
            'threads_created': 0,
            'emails_created': 0,
            'emails_updated': 0,
            'errors': 0
        }

        try:
            lookback_days = lookback_days or settings.EMAIL_SYNC_LOOKBACK_DAYS

            # Build filter for recent emails
            filter_query = None
            if not full_sync:
                after_date = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()
                filter_query = f"receivedDateTime ge {after_date}"

            # Fetch messages
            result = self.fetch_messages(max_results=500, filter_query=filter_query)
            messages = result.get('messages', [])

            logger.info(f"Syncing {len(messages)} Outlook messages")

            # Process each message
            for message in messages:
                try:
                    self._sync_single_message(message, stats)
                except Exception as e:
                    logger.error(f"Failed to sync message {message.get('id')}: {str(e)}")
                    stats['errors'] += 1

            # Log sync job
            run_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._log_sync_job('success', run_time_ms, f"Synced {stats['emails_created']} emails")

            logger.info(f"Outlook sync completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Outlook sync failed: {str(e)}")
            run_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._log_sync_job('error', run_time_ms, str(e))
            raise

    def _sync_single_message(self, message_data: Dict[str, Any], stats: Dict[str, Any]):
        """
        Sync a single message to database

        Args:
            message_data: Full message data from Graph API
            stats: Statistics dictionary to update
        """
        message_id = message_data.get('id')

        # Check if message already exists
        existing_email = (
            self.db.query(Email)
            .filter(
                Email.email_id_provider == message_id,
                Email.user_id == self.user.id
            )
            .first()
        )

        if existing_email:
            logger.debug(f"Message {message_id} already synced, skipping")
            return

        # Extract metadata
        metadata = email_parser.extract_email_metadata(message_data)

        # Extract text content
        text_content = email_parser.extract_plain_text(message_data)
        text_content = email_parser.truncate_text(text_content, 10000)

        # Parse timestamp
        received_dt_str = message_data.get('receivedDateTime')
        timestamp = datetime.fromisoformat(received_dt_str.replace('Z', '+00:00'))

        # Get or create thread
        thread = self._get_or_create_thread(
            thread_id_provider=metadata['thread_id'],
            subject=metadata['subject'],
            last_message_at=timestamp
        )

        if thread:
            stats['threads_created'] += 1

        # Store HTML content in S3/R2 (optional)
        html_url = None
        body = message_data.get('body', {})
        if body.get('contentType') == 'html':
            html_content = body.get('content', '')
            if html_content:
                html_url = storage_service.upload_email_html(
                    email_id=message_id,
                    html_content=html_content,
                    user_id=str(self.user.id)
                )

        # Create email record
        email = Email(
            thread_id=thread.id,
            user_id=self.user.id,
            email_id_provider=message_id,
            sender=metadata['from'],
            recipients=metadata['to'] + metadata['cc'],
            body_html_url=html_url,
            body_text_clean=text_content,
            timestamp=timestamp
        )

        self.db.add(email)
        self.db.commit()

        stats['emails_created'] += 1
        logger.info(f"Synced email {message_id} to thread {thread.id}")

    def _get_or_create_thread(
        self,
        thread_id_provider: str,
        subject: str,
        last_message_at: datetime
    ) -> Thread:
        """
        Get existing thread or create new one

        Args:
            thread_id_provider: Outlook conversation ID
            subject: Email subject
            last_message_at: Last message timestamp

        Returns:
            Thread instance
        """
        # Check if thread exists
        thread = (
            self.db.query(Thread)
            .filter(
                Thread.thread_id_provider == thread_id_provider,
                Thread.user_id == self.user.id
            )
            .first()
        )

        if thread:
            # Update last message time
            if last_message_at > thread.last_message_at:
                thread.last_message_at = last_message_at
                self.db.commit()
            return thread

        # Create new thread
        thread = Thread(
            user_id=self.user.id,
            thread_id_provider=thread_id_provider,
            subject=subject or "(No subject)",
            last_message_at=last_message_at
        )

        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)

        return thread

    def _log_sync_job(self, status: str, run_time_ms: int, message: str):
        """Log sync job to database"""
        log = SyncJobLog(
            user_id=self.user.id,
            provider='outlook',
            status=status,
            run_time_ms=run_time_ms,
            message=message
        )
        self.db.add(log)
        self.db.commit()

    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Outlook

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            Sent message data
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/me/sendMail"

            # Build recipients
            to_recipients = [{"emailAddress": {"address": to}}]

            message_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if is_html else "Text",
                        "content": body
                    },
                    "toRecipients": to_recipients
                }
            }

            # Add CC and BCC
            if cc:
                message_data["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc
                ]
            if bcc:
                message_data["message"]["bccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in bcc
                ]

            response = requests.post(
                url,
                headers=self._get_headers(),
                json=message_data
            )
            response.raise_for_status()

            logger.info(f"Sent email to {to}")
            return {"status": "sent", "to": to}

        except Exception as e:
            logger.error(f"Failed to send Outlook message: {str(e)}")
            raise

    def send_reply(
        self,
        message_id: str,
        body: str,
        is_html: bool = False
    ) -> Dict[str, Any]:
        """
        Send a reply to an existing message

        Args:
            message_id: Outlook message ID to reply to
            body: Reply body
            is_html: Whether body is HTML

        Returns:
            Sent reply data
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/me/messages/{message_id}/reply"

            reply_data = {
                "comment": body  # Outlook uses 'comment' for reply text
            }

            # Note: Outlook Graph API doesn't support HTML in reply comment
            # For HTML replies, we need to use createReply and send separately
            if is_html:
                return self._send_html_reply(message_id, body)

            response = requests.post(
                url,
                headers=self._get_headers(),
                json=reply_data
            )
            response.raise_for_status()

            logger.info(f"Sent reply to message {message_id}")
            return {"status": "sent", "message_id": message_id}

        except Exception as e:
            logger.error(f"Failed to send Outlook reply: {str(e)}")
            raise

    def _send_html_reply(self, message_id: str, body: str) -> Dict[str, Any]:
        """
        Send HTML reply using createReply + send workflow

        Args:
            message_id: Message ID to reply to
            body: HTML body

        Returns:
            Sent reply data
        """
        try:
            # Step 1: Create reply draft
            create_url = f"{GRAPH_API_ENDPOINT}/me/messages/{message_id}/createReply"
            response = requests.post(create_url, headers=self._get_headers())
            response.raise_for_status()

            draft = response.json()
            draft_id = draft['id']

            # Step 2: Update draft with HTML body
            update_url = f"{GRAPH_API_ENDPOINT}/me/messages/{draft_id}"
            update_data = {
                "body": {
                    "contentType": "HTML",
                    "content": body
                }
            }
            response = requests.patch(
                update_url,
                headers=self._get_headers(),
                json=update_data
            )
            response.raise_for_status()

            # Step 3: Send the draft
            send_url = f"{GRAPH_API_ENDPOINT}/me/messages/{draft_id}/send"
            response = requests.post(send_url, headers=self._get_headers())
            response.raise_for_status()

            logger.info(f"Sent HTML reply to message {message_id}")
            return {"status": "sent", "message_id": message_id, "draft_id": draft_id}

        except Exception as e:
            logger.error(f"Failed to send HTML reply: {str(e)}")
            raise

    def setup_webhook_subscription(self) -> Dict[str, Any]:
        """
        Setup Outlook webhook subscription

        Creates a webhook subscription to receive notifications when new emails arrive.

        Returns:
            Subscription response from Microsoft Graph
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/subscriptions"

            # Subscription configuration
            subscription_data = {
                "changeType": "created,updated",
                "notificationUrl": settings.OUTLOOK_WEBHOOK_URL,
                "resource": "me/mailFolders('Inbox')/messages",
                "expirationDateTime": self._get_subscription_expiration(),
                "clientState": settings.OUTLOOK_WEBHOOK_CLIENT_STATE
            }

            response = requests.post(
                url,
                headers=self._get_headers(),
                json=subscription_data
            )
            response.raise_for_status()

            subscription = response.json()

            # Store subscription ID in account metadata
            if self.account_token:
                if not self.account_token.metadata:
                    self.account_token.metadata = {}

                self.account_token.metadata['subscription_id'] = subscription['id']
                self.account_token.metadata['subscription_expiration'] = subscription['expirationDateTime']
                self.db.commit()

            logger.info(f"Outlook subscription created: {subscription['id']}")
            return subscription

        except Exception as e:
            logger.error(f"Failed to setup Outlook webhook subscription: {str(e)}")
            raise

    def renew_webhook_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Renew Outlook webhook subscription

        Extends the expiration time of an existing subscription.

        Args:
            subscription_id: Subscription ID to renew

        Returns:
            Updated subscription response
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/subscriptions/{subscription_id}"

            update_data = {
                "expirationDateTime": self._get_subscription_expiration()
            }

            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=update_data
            )
            response.raise_for_status()

            subscription = response.json()

            # Update metadata
            if self.account_token and self.account_token.metadata:
                self.account_token.metadata['subscription_expiration'] = subscription['expirationDateTime']
                self.db.commit()

            logger.info(f"Outlook subscription renewed: {subscription_id}")
            return subscription

        except Exception as e:
            logger.error(f"Failed to renew Outlook subscription: {str(e)}")
            raise

    def delete_webhook_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Delete Outlook webhook subscription

        Removes the webhook subscription.

        Args:
            subscription_id: Subscription ID to delete

        Returns:
            Response from Microsoft Graph
        """
        try:
            url = f"{GRAPH_API_ENDPOINT}/subscriptions/{subscription_id}"

            response = requests.delete(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()

            # Clear metadata
            if self.account_token and self.account_token.metadata:
                self.account_token.metadata.pop('subscription_id', None)
                self.account_token.metadata.pop('subscription_expiration', None)
                self.db.commit()

            logger.info(f"Outlook subscription deleted: {subscription_id}")
            return {"status": "deleted"}

        except Exception as e:
            logger.error(f"Failed to delete Outlook subscription: {str(e)}")
            raise

    def _get_subscription_expiration(self) -> str:
        """
        Get subscription expiration datetime

        Microsoft Graph subscriptions have a maximum lifetime of 4230 minutes (roughly 3 days).

        Returns:
            ISO 8601 formatted datetime string
        """
        from datetime import datetime, timedelta

        # Set expiration to 3 days from now
        expiration = datetime.utcnow() + timedelta(days=3)
        return expiration.isoformat() + 'Z'
