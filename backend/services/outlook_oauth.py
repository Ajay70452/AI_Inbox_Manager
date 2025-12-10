"""
Outlook OAuth Service

Handles Microsoft OAuth flow for Outlook/Microsoft Graph API access
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
import msal
import requests

from app.config import settings
from models import User, AccountToken
from utils import encrypt_token, decrypt_token
from core import ExternalServiceError

logger = logging.getLogger(__name__)

# Microsoft Graph scopes
OUTLOOK_SCOPES = [
    'https://graph.microsoft.com/Mail.ReadWrite',
    'https://graph.microsoft.com/Mail.Send',
    'https://graph.microsoft.com/User.Read'
]


class OutlookOAuthService:
    """Service for Outlook/Microsoft OAuth operations"""

    def __init__(self):
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.redirect_uri = settings.MICROSOFT_REDIRECT_URI
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"

    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate Microsoft OAuth authorization URL

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )

        auth_url = app.get_authorization_request_url(
            scopes=OUTLOOK_SCOPES,
            redirect_uri=self.redirect_uri,
            state=state,
            prompt='consent'  # Force consent to get refresh token
        )

        return auth_url

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
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )

            result = app.acquire_token_by_authorization_code(
                code=code,
                scopes=OUTLOOK_SCOPES,
                redirect_uri=self.redirect_uri
            )

            if "error" in result:
                raise ExternalServiceError(
                    f"Microsoft OAuth error: {result.get('error_description')}"
                )

            # Get user email from Microsoft Graph
            access_token = result['access_token']
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            user_data = user_response.json()
            email_address = user_data.get('mail') or user_data.get('userPrincipalName')

            # Calculate expiry time
            expires_in = result.get('expires_in', 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            return {
                'access_token': access_token,
                'refresh_token': result.get('refresh_token'),
                'expires_at': expires_at,
                'email_address': email_address,
                'scopes': result.get('scope', '').split(' ')
            }

        except Exception as e:
            logger.error(f"Outlook OAuth token exchange failed: {str(e)}")
            raise ExternalServiceError(f"Failed to connect Outlook account: {str(e)}")

    def save_tokens(
        self,
        db: Session,
        user: User,
        tokens: Dict[str, Any]
    ) -> AccountToken:
        """
        Save Outlook tokens to database

        Args:
            db: Database session
            user: User instance
            tokens: Token dictionary from exchange_code_for_tokens

        Returns:
            AccountToken instance
        """
        # Check if user already has Outlook token
        existing_token = (
            db.query(AccountToken)
            .filter(
                AccountToken.user_id == user.id,
                AccountToken.provider == 'outlook'
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
                provider='outlook',
                email_address=tokens['email_address'],
                access_token=tokens['access_token'],
                refresh_token=encrypted_refresh_token,
                expires_at=tokens['expires_at']
            )
            db.add(account_token)

        db.commit()
        db.refresh(account_token)

        logger.info(f"Outlook tokens saved for user {user.email}")
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

            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )

            result = app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=OUTLOOK_SCOPES
            )

            if "error" in result:
                raise ExternalServiceError(
                    f"Token refresh error: {result.get('error_description')}"
                )

            # Calculate expiry time
            expires_in = result.get('expires_in', 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            # Update in database
            account_token.access_token = result['access_token']
            account_token.expires_at = expires_at

            # Update refresh token if new one provided
            if 'refresh_token' in result:
                account_token.refresh_token = encrypt_token(result['refresh_token'])

            db.commit()

            logger.info(f"Outlook access token refreshed for {account_token.email_address}")
            return result['access_token']

        except Exception as e:
            logger.error(f"Outlook token refresh failed: {str(e)}")
            raise ExternalServiceError(f"Failed to refresh Outlook token: {str(e)}")

    def get_valid_access_token(
        self,
        db: Session,
        account_token: AccountToken
    ) -> str:
        """
        Get valid access token, refreshing if necessary

        Args:
            db: Database session
            account_token: AccountToken instance

        Returns:
            Valid access token string
        """
        # Check if token is expired or about to expire (within 5 minutes)
        now = datetime.utcnow()
        expires_soon = account_token.expires_at - timedelta(minutes=5)

        if now >= expires_soon:
            logger.info(f"Token expired or expiring soon, refreshing...")
            return self.refresh_access_token(db, account_token)

        return account_token.access_token

    def revoke_access(
        self,
        db: Session,
        account_token: AccountToken
    ) -> bool:
        """
        Revoke Outlook access and delete tokens

        Args:
            db: Database session
            account_token: AccountToken instance

        Returns:
            True if successful
        """
        try:
            # Microsoft doesn't have a simple revoke endpoint
            # Just delete from database
            db.delete(account_token)
            db.commit()

            logger.info(f"Outlook access revoked for {account_token.email_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke Outlook access: {str(e)}")
            return False
