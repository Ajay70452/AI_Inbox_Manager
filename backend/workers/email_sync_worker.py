"""
Email Sync Worker

Background worker for syncing emails from Gmail/Outlook
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from workers.base import BaseWorker
from models import User, AccountToken
from services import EmailSyncService
from db import SessionLocal

logger = logging.getLogger(__name__)


class EmailSyncWorker(BaseWorker):
    """Worker for syncing emails in the background"""

    def __init__(self):
        super().__init__("email_sync")

    def execute(
        self,
        user_id: str,
        provider: Optional[str] = None,
        full_sync: bool = False,
        lookback_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sync emails for a user

        Args:
            user_id: User ID to sync emails for
            provider: Specific provider (gmail/outlook) or None for all
            full_sync: If True, perform full sync
            lookback_days: Days to look back for incremental sync

        Returns:
            Sync statistics
        """
        db = SessionLocal()

        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User not found: {user_id}")

            self.logger.info(f"Syncing emails for user: {user.email}")

            # Create sync service
            sync_service = EmailSyncService(db, user)

            # Sync based on provider
            if provider == 'gmail':
                stats = sync_service.sync_gmail(lookback_days, full_sync)
            elif provider == 'outlook':
                stats = sync_service.sync_outlook(lookback_days, full_sync)
            else:
                stats = sync_service.sync_all_accounts(lookback_days, full_sync)

            self.logger.info(
                f"Email sync completed for {user.email}: "
                f"{stats.get('total_emails', 0)} emails, "
                f"{stats.get('total_threads', 0)} threads"
            )

            return stats

        except Exception as e:
            self.logger.error(f"Email sync failed for user {user_id}: {str(e)}")
            raise

        finally:
            db.close()


class BulkEmailSyncWorker(BaseWorker):
    """Worker for syncing emails for multiple users"""

    def __init__(self):
        super().__init__("bulk_email_sync")

    def execute(self, lookback_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Sync emails for all users with connected accounts

        Args:
            lookback_days: Days to look back

        Returns:
            Aggregated sync statistics
        """
        db = SessionLocal()

        try:
            # Get all users with connected accounts
            users_with_accounts = (
                db.query(User)
                .join(AccountToken)
                .distinct()
                .all()
            )

            self.logger.info(f"Starting bulk sync for {len(users_with_accounts)} users")

            total_stats = {
                'users_synced': 0,
                'users_failed': 0,
                'total_emails': 0,
                'total_threads': 0,
                'errors': []
            }

            # Sync each user
            for user in users_with_accounts:
                try:
                    sync_service = EmailSyncService(db, user)
                    stats = sync_service.sync_all_accounts(lookback_days, full_sync=False)

                    total_stats['users_synced'] += 1
                    total_stats['total_emails'] += stats.get('total_emails', 0)
                    total_stats['total_threads'] += stats.get('total_threads', 0)

                    if stats.get('errors'):
                        total_stats['errors'].extend(stats['errors'])

                except Exception as e:
                    self.logger.error(f"Failed to sync user {user.email}: {str(e)}")
                    total_stats['users_failed'] += 1
                    total_stats['errors'].append(f"{user.email}: {str(e)}")

            self.logger.info(
                f"Bulk sync completed: {total_stats['users_synced']} users, "
                f"{total_stats['total_emails']} emails"
            )

            return total_stats

        finally:
            db.close()


# Standalone functions for RQ/Celery
def sync_user_emails(
    user_id: str,
    provider: Optional[str] = None,
    full_sync: bool = False,
    lookback_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sync emails for a user (standalone function for job queues)

    Args:
        user_id: User ID
        provider: Provider to sync (gmail/outlook) or None for all
        full_sync: If True, perform full sync
        lookback_days: Days to look back

    Returns:
        Sync statistics
    """
    worker = EmailSyncWorker()
    return worker.run(user_id, provider, full_sync, lookback_days)


def sync_all_users(lookback_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Sync emails for all users (standalone function for job queues)

    Args:
        lookback_days: Days to look back

    Returns:
        Aggregated statistics
    """
    worker = BulkEmailSyncWorker()
    return worker.run(lookback_days)
