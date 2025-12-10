"""
Email Sync Tests

Tests for email synchronization functionality
"""

import pytest
from unittest.mock import Mock, patch
from models import AccountToken, Thread, Email
from services.gmail_service import GmailService


@pytest.fixture
def gmail_account(db_session, test_user):
    """Create a test Gmail account token"""
    account = AccountToken(
        user_id=test_user.id,
        provider='gmail',
        email='test@gmail.com',
        access_token='test_access_token',
        refresh_token='test_refresh_token',
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


def test_trigger_email_sync(client, test_user, auth_headers, gmail_account):
    """Test triggering email sync"""
    with patch('services.EmailSyncService.sync_gmail') as mock_sync:
        mock_sync.return_value = {
            'threads_created': 5,
            'emails_created': 10,
            'emails_updated': 0,
            'errors': 0
        }

        response = client.post(
            "/api/v1/emails/sync?provider=gmail",
            json={"force": False},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data


def test_sync_status(client, test_user, auth_headers, gmail_account):
    """Test getting sync status"""
    response = client.get(
        "/api/v1/emails/sync/status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_email_by_id(client, test_user, auth_headers, db_session, gmail_account):
    """Test getting a single email by ID"""
    # Create a test thread and email
    thread = Thread(
        user_id=test_user.id,
        thread_id_provider='test_thread_123',
        subject='Test Email',
        last_message_at='2024-01-01T00:00:00'
    )
    db_session.add(thread)
    db_session.commit()
    db_session.refresh(thread)

    email = Email(
        thread_id=thread.id,
        user_id=test_user.id,
        email_id_provider='test_email_123',
        sender='sender@example.com',
        recipients=['recipient@example.com'],
        body_text_clean='Test email body',
        timestamp='2024-01-01T00:00:00'
    )
    db_session.add(email)
    db_session.commit()
    db_session.refresh(email)

    response = client.get(
        f"/api/v1/emails/{email.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email_id_provider"] == 'test_email_123'
    assert data["sender"] == 'sender@example.com'


def test_get_nonexistent_email(client, test_user, auth_headers):
    """Test getting an email that doesn't exist"""
    response = client.get(
        "/api/v1/emails/nonexistent_id",
        headers=auth_headers
    )

    assert response.status_code == 404
