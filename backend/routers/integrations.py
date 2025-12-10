from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db import get_db
from models import User, Integration
from schemas import IntegrationResponse, SlackAlertRequest, TaskIntegrationRequest
from app.dependencies import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Slack Integration
@router.get("/slack/start")
def slack_oauth_start(current_user: User = Depends(get_current_user)):
    """Start Slack OAuth flow"""
    # TODO: Implement Slack OAuth
    return {"message": "Slack OAuth start - implementation pending"}


@router.get("/slack/callback")
def slack_oauth_callback(code: str, current_user: User = Depends(get_current_user)):
    """Handle Slack OAuth callback"""
    # TODO: Implement Slack OAuth callback
    return {"message": "Slack OAuth callback - implementation pending"}


@router.post("/slack/test")
def test_slack_connection(current_user: User = Depends(get_current_user)):
    """Test Slack connection"""
    # TODO: Test Slack integration
    return {"message": "Slack connection test - implementation pending"}


@router.post("/slack/alert")
def send_slack_alert(
    alert_request: SlackAlertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send manual Slack alert for a thread"""
    # TODO: Implement Slack alert sending
    logger.info(f"Slack alert requested for thread: {alert_request.thread_id}")
    return {"message": "Slack alert sent - implementation pending"}


# Generic Integration Endpoints
@router.get("/{tool}/start")
def integration_oauth_start(
    tool: str,
    current_user: User = Depends(get_current_user),
):
    """
    Start OAuth flow for integration

    Supported tools: notion, clickup, jira, trello
    """
    # TODO: Implement OAuth for various tools
    return {"message": f"{tool} OAuth start - implementation pending"}


@router.get("/{tool}/callback")
def integration_oauth_callback(
    tool: str,
    code: str,
    current_user: User = Depends(get_current_user),
):
    """Handle OAuth callback for integration"""
    # TODO: Implement OAuth callback
    return {"message": f"{tool} OAuth callback - implementation pending"}


@router.post("/{tool}/task")
def create_task_in_tool(
    tool: str,
    task_request: TaskIntegrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create task in external tool

    Supported tools: notion, clickup, jira, trello
    """
    # TODO: Implement task creation in external tools
    logger.info(f"Task creation requested in {tool} for task: {task_request.task_id}")
    return {"message": f"Task creation in {tool} - implementation pending"}


@router.get("/", response_model=List[IntegrationResponse])
def list_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all active integrations for current user"""
    integrations = (
        db.query(Integration)
        .filter(Integration.user_id == current_user.id)
        .all()
    )
    return integrations
