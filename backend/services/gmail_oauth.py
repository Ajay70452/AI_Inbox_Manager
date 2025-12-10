"""
Gmail OAuth Service

Handles Google OAuth flow for Gmail API access
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import settings
from models import User, AccountToken
from utils import encrypt_token, decrypt_token
from core import ExternalServiceError

logger = logging.getLogger(__name__)

# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailOAuthService:
    """Service for Gmail OAuth operations"""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Gmail OAuth authorization URL

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=GMAIL_SCOPES,
            redirect_uri=self.redirect_uri
        )

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent to get refresh token
            state=state
        )

        return authorization_url

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Dictionary with tokens and user info

        Raises:
            ExternalServiceError: If token exchange fails
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=GMAIL_SCOPES,
                redirect_uri=self.redirect_uri
            )

            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Get user email
            gmail_service = build('gmail', 'v1', credentials=credentials)
            profile = gmail_service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress')

            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry,
                'email_address': email_address,
                'scopes': credentials.scopes
            }

        except Exception as e:
            logger.error(f"Gmail OAuth token exchange failed: {str(e)}")
            raise ExternalServiceError(f"Failed to connect Gmail account: {str(e)}")

    def save_tokens(
        self,
        db: Session,
        user: User,
        tokens: Dict[str, Any]
    ) -> AccountToken:
        """
        Save Gmail tokens to database

        Args:
            db: Database session
            user: User instance
            tokens: Token dictionary from exchange_code_for_tokens

        Returns:
            AccountToken instance
        """
        # Check if user already has Gmail token
        existing_token = (
            db.query(AccountToken)
            .filter(
                AccountToken.user_id == user.id,
                AccountToken.provider == 'gmail'
            )
            .first()
        )

        # Encrypt refresh token
        encrypted_refresh_token = encrypt_token(tokens['refresh_token'])

        if existing_token:
            # Update existing token
            existing_token.access_token = tokens['access_token']
            existing_token.refresh_token = encrypted_refresh_token
            existing_token.expires_at = tokens['expires_at']
            existing_token.email_address = tokens['email_address']
            account_token = existing_token
        else:
            # Create new token
            account_token = AccountToken(
                user_id=user.id,
                provider='gmail',
                email_address=tokens['email_address'],
                access_token=tokens['access_token'],
                refresh_token=encrypted_refresh_token,
                expires_at=tokens['expires_at']
            )
            db.add(account_token)

        db.commit()
        db.refresh(account_token)

        logger.info(f"Gmail tokens saved for user {user.email}")
        return account_token

    def refresh_access_token(
        self,
        db: Session,
        account_token: AccountToken
    ) -> str:
        """
        Refresh access token using refresh token

        Args:
            db: Database session
            account_token: AccountToken instance

        Returns:
            New access token

        Raises:
            ExternalServiceError: If refresh fails
        """
        try:
            # Decrypt refresh token
            refresh_token = decrypt_token(account_token.refresh_token)

            # Create credentials with refresh token
            credentials = Credentials(
                token=account_token.access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            # Refresh the token
            from google.auth.transport.requests import Request
            credentials.refresh(Request())

            # Update in database
            account_token.access_token = credentials.token
            account_token.expires_at = credentials.expiry
            db.commit()

            logger.info(f"Gmail access token refreshed for {account_token.email_address}")
            return credentials.token

        except Exception as e:
            logger.error(f"Gmail token refresh failed: {str(e)}")
            raise ExternalServiceError(f"Failed to refresh Gmail token: {str(e)}")

    def get_valid_credentials(
        self,
        db: Session,
        account_token: AccountToken
    ) -> Credentials:
        """
        Get valid credentials, refreshing if necessary

        Args:
            db: Database session
            account_token: AccountToken instance

        Returns:
            Valid Google Credentials object
        """
        # Check if token is expired or about to expire (within 5 minutes)
        now = datetime.utcnow()
        expires_soon = account_token.expires_at - timedelta(minutes=5)

        if now >= expires_soon:
            logger.info(f"Token expired or expiring soon, refreshing...")
            self.refresh_access_token(db, account_token)

        # Decrypt refresh token
        refresh_token = decrypt_token(account_token.refresh_token)

        credentials = Credentials(
            token=account_token.access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        return credentials

    def revoke_access(
        self,
        db: Session,
        account_token: AccountToken
    ) -> bool:
        """
        Revoke Gmail access and delete tokens

        Args:
            db: Database session
            account_token: AccountToken instance

        Returns:
            True if successful
        """
        try:
            # Revoke token with Google
            credentials = self.get_valid_credentials(db, account_token)
            from google.auth.transport.requests import Request
            credentials.revoke(Request())

            # Delete from database
            db.delete(account_token)
            db.commit()

            logger.info(f"Gmail access revoked for {account_token.email_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke Gmail access: {str(e)}")
            return False
