"""
Email Sync Orchestrator

Coordinates email syncing from multiple providers (Gmail, Outlook)
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models import User, AccountToken
from services.gmail_service import GmailService
from services.outlook_service import OutlookService

logger = logging.getLogger(__name__)


class EmailSyncService:
    """Main service for coordinating email sync across providers"""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    def sync_all_accounts(
        self,
        lookback_days: Optional[int] = None,
        full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync all connected email accounts for user

        Args:
            lookback_days: Days to look back for emails
            full_sync: If True, perform full sync

        Returns:
            Combined sync statistics
        """
        results = {
            'gmail': None,
            'outlook': None,
            'total_emails': 0,
            'total_threads': 0,
            'errors': []
        }

        # Check for connected accounts
        accounts = (
            self.db.query(AccountToken)
            .filter(AccountToken.user_id == self.user.id)
            .all()
        )

        for account in accounts:
            provider = account.provider

            try:
                if provider == 'gmail':
                    logger.info(f"Starting Gmail sync for user {self.user.email}")
                    gmail_service = GmailService(self.db, self.user)
                    stats = gmail_service.sync_emails(lookback_days, full_sync)
                    results['gmail'] = stats
                    results['total_emails'] += stats.get('emails_created', 0)
                    results['total_threads'] += stats.get('threads_created', 0)

                elif provider == 'outlook':
                    logger.info(f"Starting Outlook sync for user {self.user.email}")
                    outlook_service = OutlookService(self.db, self.user)
                    stats = outlook_service.sync_emails(lookback_days, full_sync)
                    results['outlook'] = stats
                    results['total_emails'] += stats.get('emails_created', 0)
                    results['total_threads'] += stats.get('threads_created', 0)

            except Exception as e:
                error_msg = f"Failed to sync {provider}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        logger.info(
            f"Email sync completed for user {self.user.email}: "
            f"{results['total_emails']} emails, {results['total_threads']} threads"
        )

        return results

    def sync_gmail(
        self,
        lookback_days: Optional[int] = None,
        full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync Gmail account only

        Args:
            lookback_days: Days to look back
            full_sync: If True, perform full sync

        Returns:
            Sync statistics
        """
        logger.info(f"Starting Gmail sync for user {self.user.email}")
        gmail_service = GmailService(self.db, self.user)
        return gmail_service.sync_emails(lookback_days, full_sync)

    def sync_outlook(
        self,
        lookback_days: Optional[int] = None,
        full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync Outlook account only

        Args:
            lookback_days: Days to look back
            full_sync: If True, perform full sync

        Returns:
            Sync statistics
        """
        logger.info(f"Starting Outlook sync for user {self.user.email}")
        outlook_service = OutlookService(self.db, self.user)
        return outlook_service.sync_emails(lookback_days, full_sync)

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get sync status for user's accounts

        Returns:
            Dictionary with sync status for each provider
        """
        from models import SyncJobLog

        status = {
            'gmail': {'connected': False, 'last_sync': None, 'status': None},
            'outlook': {'connected': False, 'last_sync': None, 'status': None}
        }

        # Check connected accounts
        accounts = (
            self.db.query(AccountToken)
            .filter(AccountToken.user_id == self.user.id)
            .all()
        )

        for account in accounts:
            provider = account.provider
            status[provider]['connected'] = True
            status[provider]['email_address'] = account.email_address

            # Get last sync log
            last_log = (
                self.db.query(SyncJobLog)
                .filter(
                    SyncJobLog.user_id == self.user.id,
                    SyncJobLog.provider == provider
                )
                .order_by(SyncJobLog.created_at.desc())
                .first()
            )

            if last_log:
                status[provider]['last_sync'] = last_log.created_at.isoformat()
                status[provider]['status'] = last_log.status
                status[provider]['message'] = last_log.message
                status[provider]['run_time_ms'] = last_log.run_time_ms

        return status
