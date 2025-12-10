from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from db import get_db
from models import User
from schemas import UserSignup, UserLogin, Token, OAuth2CallbackResponse
from app.dependencies import get_current_user
from core import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    ConflictError,
    AuthenticationError,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=Token)
@router.post("/register", response_model=Token)  # Alias for frontend compatibility
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    User signup endpoint

    Creates a new user account and returns JWT tokens
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ConflictError("Email already registered")

    # Create new user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user created: {new_user.email}")

    # Generate tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    User login endpoint

    Authenticates user and returns JWT tokens
    """
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise AuthenticationError("Invalid email or password")

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    logger.info(f"User logged in: {user.email}")

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }


# Helper to get user from token query param (for OAuth redirects)
def get_user_from_token(token: str = None, db: Session = Depends(get_db)) -> User:
    """Get user from token query parameter"""
    from core.security import decode_token

    logger.info(f"get_user_from_token called with token present: {token is not None}")

    if not token:
        logger.error("No token provided in query parameter")
        raise AuthenticationError("No token provided")

    payload = decode_token(token)
    if payload is None:
        logger.error("Failed to decode token")
        raise AuthenticationError("Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        logger.error("No user_id in token payload")
        raise AuthenticationError("Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User not found for id: {user_id}")
        raise AuthenticationError("User not found")

    logger.info(f"Successfully authenticated user: {user.email}")
    return user


# OAuth endpoints
@router.get("/google/start", dependencies=[])
@router.get("/gmail/authorize", dependencies=[])  # Alias for frontend compatibility
def google_oauth_start(token: str = None, db: Session = Depends(get_db)):
    """
    Start Google OAuth flow
    Redirects to Google OAuth consent screen
    """
    from services import GmailOAuthService

    logger.info(f"google_oauth_start called with token={token is not None}")

    try:
        # Get user from token query parameter
        current_user = get_user_from_token(token, db)

        oauth_service = GmailOAuthService()
        auth_url = oauth_service.get_authorization_url(state=str(current_user.id))

        logger.info(f"Redirecting user {current_user.email} to Google OAuth")
        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"Failed to start Google OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start Gmail authentication: {str(e)}"
        )


@router.get("/google/callback", dependencies=[])
def google_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback
    Exchanges code for tokens and stores them
    """
    from services import GmailOAuthService

    try:
        # Get user from state parameter
        user = db.query(User).filter(User.id == state).first()
        if not user:
            raise AuthenticationError("Invalid state parameter")

        oauth_service = GmailOAuthService()

        # Exchange code for tokens
        tokens = oauth_service.exchange_code_for_tokens(code)

        # Save tokens
        oauth_service.save_tokens(db, user, tokens)

        logger.info(f"Gmail connected for user {user.email}: {tokens['email_address']}")

        return OAuth2CallbackResponse(
            success=True,
            message=f"Gmail account connected: {tokens['email_address']}",
            provider="gmail",
            email_address=tokens['email_address']
        )

    except Exception as e:
        logger.error(f"Gmail OAuth callback failed: {str(e)}")
        return OAuth2CallbackResponse(
            success=False,
            message=f"Failed to connect Gmail: {str(e)}",
            provider="gmail"
        )


@router.get("/outlook/start", dependencies=[])
@router.get("/outlook/authorize", dependencies=[])  # Alias for frontend compatibility
def outlook_oauth_start(token: str = None, db: Session = Depends(get_db)):
    """
    Start Microsoft OAuth flow
    Redirects to Microsoft OAuth consent screen
    """
    from services import OutlookOAuthService

    try:
        # Get user from token query parameter
        current_user = get_user_from_token(token, db)

        oauth_service = OutlookOAuthService()
        auth_url = oauth_service.get_authorization_url(state=str(current_user.id))

        logger.info(f"Redirecting user {current_user.email} to Microsoft OAuth")
        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"Failed to start Microsoft OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start Outlook authentication: {str(e)}"
        )


@router.get("/outlook/callback", dependencies=[])
def outlook_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Microsoft OAuth callback
    Exchanges code for tokens and stores them
    """
    from services import OutlookOAuthService

    try:
        # Get user from state parameter
        user = db.query(User).filter(User.id == state).first()
        if not user:
            raise AuthenticationError("Invalid state parameter")

        oauth_service = OutlookOAuthService()

        # Exchange code for tokens
        tokens = oauth_service.exchange_code_for_tokens(code)

        # Save tokens
        oauth_service.save_tokens(db, user, tokens)

        logger.info(f"Outlook connected for user {user.email}: {tokens['email_address']}")

        return OAuth2CallbackResponse(
            success=True,
            message=f"Outlook account connected: {tokens['email_address']}",
            provider="outlook",
            email_address=tokens['email_address']
        )

    except Exception as e:
        logger.error(f"Outlook OAuth callback failed: {str(e)}")
        return OAuth2CallbackResponse(
            success=False,
            message=f"Failed to connect Outlook: {str(e)}",
            provider="outlook"
        )


@router.get("/accounts")
def get_connected_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of connected email accounts for the current user

    Returns:
        List of connected accounts with provider and email information
    """
    from models import AccountToken

    try:
        # Get all account tokens for the user
        account_tokens = db.query(AccountToken).filter(
            AccountToken.user_id == current_user.id
        ).all()

        accounts = []
        for token in account_tokens:
            accounts.append({
                "id": str(token.id),
                "provider": token.provider,
                "email_address": token.email_address,
                "is_active": True,  # You can add an is_active field to the model later
                "connected_at": token.created_at.isoformat() if token.created_at else None
            })

        return {"accounts": accounts}
    
    except Exception as e:
        logger.error(f"Failed to get connected accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connected accounts"
        )


@router.get("/extension-login-success", include_in_schema=False)
async def extension_login_success(access_token: str, refresh_token: str):
    """
    Handles successful login for Chrome extension.
    Sends tokens back to the extension using window.postMessage.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login Success</title>
        <script>
            window.onload = function() {{
                if (window.opener) {{
                    const message = {{
                        type: 'INBOX_MANAGER_AUTH_SUCCESS',
                        access_token: '{access_token}',
                        refresh_token: '{refresh_token}'
                    }};
                    // Replace '*' with the actual Chrome extension ID for security in production
                    // During development, '*' might be acceptable if the extension's origin is dynamic.
                    // For example: 'chrome-extension://YOUR_EXTENSION_ID'
                    window.opener.postMessage(message, '*');
                    window.close();
                }} else {{
                    document.body.innerHTML = '<h1>Login Successful!</h1><p>You can close this window.</p>';
                }}
            }};
        </script>
    </head>
    <body>
        <p>Processing login...</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
