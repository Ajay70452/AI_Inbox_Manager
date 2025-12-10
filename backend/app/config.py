from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AI Inbox Manager"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_URL: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str
    REDIS_QUEUE_NAME: str = "ai_inbox_queue"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OAuth - Google (Gmail)
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # OAuth - Microsoft (Outlook)
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_REDIRECT_URI: str
    MICROSOFT_TENANT_ID: str = "common"

    # OpenAI API
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Additional LLM APIs
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    DEFAULT_LLM_PROVIDER: str = "gemini"
    DEFAULT_LLM_MODEL: str = "gemini-1.5-flash"

    # Storage (S3 / CloudFlare R2)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "ai-inbox-emails"

    # Slack Integration
    SLACK_CLIENT_ID: str | None = None
    SLACK_CLIENT_SECRET: str | None = None
    SLACK_SIGNING_SECRET: str | None = None

    # ClickUp Integration
    CLICKUP_CLIENT_ID: str | None = None
    CLICKUP_CLIENT_SECRET: str | None = None

    # Notion Integration
    NOTION_CLIENT_ID: str | None = None
    NOTION_CLIENT_SECRET: str | None = None

    # Jira Integration
    JIRA_CLIENT_ID: str | None = None
    JIRA_CLIENT_SECRET: str | None = None

    # Trello Integration
    TRELLO_API_KEY: str | None = None
    TRELLO_API_SECRET: str | None = None

    # Email Sync Settings
    EMAIL_SYNC_INTERVAL_MINUTES: int = 5
    EMAIL_SYNC_LOOKBACK_DAYS: int = 90

    # Gmail Webhooks
    GMAIL_PUBSUB_TOPIC: str = "projects/your-project-id/topics/gmail-push"

    # Outlook Webhooks
    OUTLOOK_WEBHOOK_URL: str = "https://your-domain.com/api/v1/webhooks/outlook/push"
    OUTLOOK_WEBHOOK_CLIENT_STATE: str  # Secret string to verify webhook authenticity

    # AI Processing
    AI_PROCESSING_INTERVAL_MINUTES: int = 60  # Increased to reduce API usage
    AI_PROCESSING_BATCH_SIZE: int = 5         # Reduced to prevent quota exhaustion
    AI_CONTEXT_MAX_TOKENS: int = 8000
    AI_TEMPERATURE: float = 0.7

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "*"  # Allow all origins for development/extension
    ]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
