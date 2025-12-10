"""
Services package

Contains all business logic services:
- AI orchestration
- Email processing
- Integrations
"""

# AI Services
from .ai_orchestrator import AIOrchestrator
from .llm_providers import OpenAIProvider, get_llm_provider, parse_json_response
from .prompts import PromptTemplates
from .summarizer import SummarizationService
from .classifier import ClassificationService
from .sentiment_analyzer import SentimentAnalysisService
from .reply_generator import ReplyGenerationService
from .task_extractor import TaskExtractionService

# Email Sync Services
from .gmail_oauth import GmailOAuthService
from .outlook_oauth import OutlookOAuthService
from .gmail_service import GmailService
from .outlook_service import OutlookService
from .email_sync_service import EmailSyncService

__all__ = [
    # AI Services
    "AIOrchestrator",
    "OpenAIProvider",
    "get_llm_provider",
    "parse_json_response",
    "PromptTemplates",
    "SummarizationService",
    "ClassificationService",
    "SentimentAnalysisService",
    "ReplyGenerationService",
    "TaskExtractionService",
    # Email Sync Services
    "GmailOAuthService",
    "OutlookOAuthService",
    "GmailService",
    "OutlookService",
    "EmailSyncService",
]
