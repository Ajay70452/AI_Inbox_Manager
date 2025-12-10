"""
Gmail Service

Handles fetching and syncing emails from Gmail API
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from googleapiclient.discovery import build

from models import User, AccountToken, Thread, Email, SyncJobLog
from services.gmail_oauth import GmailOAuthService
from utils import email_parser, storage_service
from app.config import settings

logger = logging.getLogger(__name__)


class GmailService:
    """Service for Gmail email operations"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.oauth_service = GmailOAuthService()
        self.account_token = self._get_account_token()

    def _get_account_token(self) -> Optional[AccountToken]:
        """Get user's Gmail account token"""
        return (
            self.db.query(AccountToken)
            .filter(
                AccountToken.user_id == self.user.id,
                AccountToken.provider == 'gmail'
            )
            .first()
        )

    def _get_gmail_service(self):
        """Get authenticated Gmail API service"""
        if not self.account_token:
            raise ValueError("Gmail account not connected")

        credentials = self.oauth_service.get_valid_credentials(
            self.db,
            self.account_token
        )

        return build('gmail', 'v1', credentials=credentials)

    def fetch_messages(
        self,
        max_results: int = 100,
        page_token: Optional[str] = None,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch messages from Gmail

        Args:
            max_results: Maximum messages to fetch (max 500)
            page_token: Page token for pagination
            query: Gmail search query (e.g., "is:unread")

        Returns:
            Dictionary with messages and nextPageToken
        """
        service = self._get_gmail_service()

        try:
            params = {
                'userId': 'me',
                'maxResults': min(max_results, 500)
            }

            if page_token:
                params['pageToken'] = page_token

            if query:
                params['q'] = query

            result = service.users().messages().list(**params).execute()

            messages = result.get('messages', [])
            next_page_token = result.get('nextPageToken')

            logger.info(f"Fetched {len(messages)} messages from Gmail")

            return {
                'messages': messages,
                'nextPageToken': next_page_token
            }

        except Exception as e:
            logger.error(f"Failed to fetch Gmail messages: {str(e)}")
            raise

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get full message details from Gmail

        Args:
            message_id: Gmail message ID

        Returns:
            Full message data
        """
        service = self._get_gmail_service()

        try:
            message = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            return message

        except Exception as e:
            logger.error(f"Failed to get Gmail message {message_id}: {str(e)}")
            raise

    def resolve_thread_id(self, thread_id: str) -> Optional[str]:
        """
        Resolve a potential alias/base64 thread ID to the canonical hex ID
        
        Args:
            thread_id: Thread ID to resolve
            
        Returns:
            Canonical hex ID or None if not found
        """
        service = self._get_gmail_service()
        try:
            # Fetch minimal thread details just to get the ID
            # Note: Gmail API 'get' method automatically resolves aliases to canonical IDs
            gmail_thread = service.users().threads().get(
                userId='me', 
                id=thread_id,
                format='minimal'
            ).execute()
            
            if gmail_thread:
                return gmail_thread.get('id')
            return None
        except Exception as e:
            # If it's a 404, it might be because the ID is invalid or not found
            # But sometimes the "new" IDs are not resolvable via the API directly if they are not hex
            # However, the API usually accepts the hex ID.
            # If we are here, it means the API call failed.
            logger.warning(f"Failed to resolve thread ID {thread_id}: {e}")
            return None

    def sync_thread(self, thread_id: str) -> Optional[str]:
        """
        Sync a specific thread from Gmail

        Args:
            thread_id: Gmail thread ID

        Returns:
            Canonical Thread ID (hex) if successful, None otherwise
        """
        service = self._get_gmail_service()
        
        try:
            # Fetch thread details (minimal to get message IDs)
            gmail_thread = service.users().threads().get(
                userId='me', 
                id=thread_id,
                format='minimal'
            ).execute()
            
            if not gmail_thread:
                logger.warning(f"Thread {thread_id} not found in Gmail")
                return None
                
            # Get canonical ID (hex format)
            canonical_id = gmail_thread.get('id')
                
            messages = gmail_thread.get('messages', [])
            if not messages:
                logger.warning(f"Thread {thread_id} has no messages")
                return None
                
            logger.info(f"Syncing thread {thread_id} (canonical: {canonical_id}) with {len(messages)} messages")
            
            stats = {'emails_created': 0, 'threads_created': 0, 'errors': 0}
            
            for msg in messages:
                try:
                    self._sync_single_message(msg['id'], stats)
                except Exception as e:
                    logger.error(f"Failed to sync message {msg['id']} in thread {thread_id}: {str(e)}")
            
            return canonical_id
            
        except Exception as e:
            logger.error(f"Failed to sync thread {thread_id}: {str(e)}")
            return None

    def sync_emails(
        self,
        lookback_days: Optional[int] = None,
        full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync emails from Gmail to database

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

            # Build query for recent emails
            after_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime('%Y/%m/%d')
            query = f"after:{after_date}" if not full_sync else None

            # Fetch messages
            result = self.fetch_messages(max_results=500, query=query)
            message_ids = [msg['id'] for msg in result.get('messages', [])]

            logger.info(f"Syncing {len(message_ids)} Gmail messages")

            # Process each message
            for msg_id in message_ids:
                try:
                    self._sync_single_message(msg_id, stats)
                except Exception as e:
                    logger.error(f"Failed to sync message {msg_id}: {str(e)}")
                    stats['errors'] += 1

            # Log sync job
            run_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._log_sync_job('success', run_time_ms, f"Synced {stats['emails_created']} emails")

            logger.info(f"Gmail sync completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Gmail sync failed: {str(e)}")
            run_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self._log_sync_job('error', run_time_ms, str(e))
            raise

    def _sync_single_message(self, message_id: str, stats: Dict[str, Any]):
        """
        Sync a single message to database

        Args:
            message_id: Gmail message ID
            stats: Statistics dictionary to update
        """
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

        # Fetch full message data
        message_data = self.get_message(message_id)

        # Extract metadata
        metadata = email_parser.extract_email_metadata(message_data)

        # Extract text content
        text_content = email_parser.extract_plain_text(message_data)
        text_content = email_parser.truncate_text(text_content, 10000)

        # Get or create thread
        thread = self._get_or_create_thread(
            thread_id_provider=metadata['thread_id'],
            subject=metadata['subject'],
            last_message_at=datetime.utcnow()  # We'll parse the actual date later
        )

        if thread:
            stats['threads_created'] += 1

        # Store HTML content in S3/R2 (optional)
        html_url = None
        if message_data.get('payload'):
            # Extract HTML if available
            html_content = self._extract_html_content(message_data['payload'])
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
            timestamp=datetime.utcnow()  # Parse from metadata['date'] if needed
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
            thread_id_provider: Gmail thread ID
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

    def _extract_html_content(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract HTML content from Gmail payload"""
        # Check if single part HTML
        if payload.get('mimeType') == 'text/html' and payload.get('body', {}).get('data'):
            return email_parser.decode_base64(payload['body']['data'])

        # Check multipart
        if 'parts' in payload:
            for part in payload['parts']:
                if 'parts' in part:
                    html = self._extract_html_content(part)
                    if html:
                        return html
                elif part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
                    return email_parser.decode_base64(part['body']['data'])

        return None

    def _log_sync_job(self, status: str, run_time_ms: int, message: str):
        """Log sync job to database"""
        log = SyncJobLog(
            user_id=self.user.id,
            provider='gmail',
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
        thread_id: Optional[str] = None,
        message_id: Optional[str] = None,
        references: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            thread_id: Gmail thread ID to reply to (for threading)
            message_id: Original message ID (for In-Reply-To header)
            references: References header for email threading
            cc: CC recipients
            bcc: BCC recipients
            html: Whether body is HTML

        Returns:
            Sent message data
        """
        service = self._get_gmail_service()

        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64

            # Create message
            if html:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(body, 'html'))
            else:
                message = MIMEText(body, 'plain')

            message['to'] = to
            message['subject'] = subject

            # Add CC and BCC
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)

            # Add threading headers for replies
            if message_id:
                message['In-Reply-To'] = message_id
            if references:
                message['References'] = references

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send with thread ID if replying
            body_data = {'raw': raw}
            if thread_id:
                body_data['threadId'] = thread_id

            result = service.users().messages().send(
                userId='me',
                body=body_data
            ).execute()

            logger.info(f"Sent email to {to}: {result['id']}")
            return result

        except Exception as e:
            logger.error(f"Failed to send Gmail message: {str(e)}")
            raise

    def send_reply(
        self,
        thread_id: str,
        body: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send a reply to an existing thread

        Args:
            thread_id: Thread ID to reply to
            body: Reply body
            html: Whether body is HTML

        Returns:
            Sent message data
        """
        # Get the thread to extract recipient and subject
        thread = (
            self.db.query(Thread)
            .filter(
                Thread.thread_id_provider == thread_id,
                Thread.user_id == self.user.id
            )
            .first()
        )

        if not thread:
            raise ValueError(f"Thread not found: {thread_id}")

        # Get the latest email in the thread
        latest_email = (
            self.db.query(Email)
            .filter(Email.thread_id == thread.id)
            .order_by(Email.received_at.desc())
            .first()
        )

        if not latest_email:
            raise ValueError(f"No emails found in thread: {thread_id}")

        # Extract recipient (reply to sender)
        # Parse from_email from latest_email.from_email
        to_email = latest_email.from_email

        # Build subject with Re: prefix if not already present
        subject = thread.subject
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"

        # Build References header (for proper threading)
        references = latest_email.message_id if latest_email.message_id else None

        return self.send_message(
            to=to_email,
            subject=subject,
            body=body,
            thread_id=thread_id,
            message_id=latest_email.message_id,
            references=references,
            html=html
        )

    def setup_push_notifications(self) -> Dict[str, Any]:
        """
        Setup Gmail push notifications

        Configures Gmail to send push notifications to our webhook endpoint
        when new emails arrive.

        Returns:
            Watch response from Gmail API
        """
        service = self._get_gmail_service()

        try:
            # Setup watch request
            request_body = {
                'topicName': settings.GMAIL_PUBSUB_TOPIC,
                'labelIds': ['INBOX']
            }

            watch_response = service.users().watch(
                userId='me',
                body=request_body
            ).execute()

            # Store history_id in account metadata for incremental sync
            if self.account_token and watch_response.get('historyId'):
                if not self.account_token.metadata:
                    self.account_token.metadata = {}

                self.account_token.metadata['history_id'] = watch_response['historyId']
                self.account_token.metadata['watch_expiration'] = watch_response.get('expiration')
                self.db.commit()

            logger.info(f"Gmail watch setup successful: {watch_response}")
            return watch_response

        except Exception as e:
            logger.error(f"Failed to setup Gmail push notifications: {str(e)}")
            raise

    def stop_push_notifications(self) -> Dict[str, Any]:
        """
        Stop Gmail push notifications

        Stops the watch on the user's mailbox.

        Returns:
            Response from Gmail API
        """
        service = self._get_gmail_service()

        try:
            service.users().stop(userId='me').execute()

            # Clear metadata
            if self.account_token:
                if self.account_token.metadata:
                    self.account_token.metadata.pop('history_id', None)
                    self.account_token.metadata.pop('watch_expiration', None)
                    self.db.commit()

            logger.info("Gmail watch stopped successfully")
            return {"status": "stopped"}

        except Exception as e:
            logger.error(f"Failed to stop Gmail push notifications: {str(e)}")
            raise
