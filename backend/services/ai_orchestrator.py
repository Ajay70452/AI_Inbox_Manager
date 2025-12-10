"""
AI Orchestration Layer - The "Secret Sauce"

This module coordinates all AI operations:
- Fetches thread data and company context
- Builds prompts with context injection
- Routes requests to appropriate LLM
- Handles retries and rate limiting
- Ensures consistent structured output
- Manages token limits
"""

import logging
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from models import Thread, Email, CompanyContext, User
from services.prompts import PromptTemplates
from services.llm_providers import get_llm_provider, parse_json_response
from app.config import settings
from core import ExternalServiceError

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    The AI Orchestration Layer

    This class is responsible for:
    1. Fetching relevant context (company info, thread history)
    2. Building intelligent prompts
    3. Managing LLM interactions
    4. Handling errors and retries
    """

    def __init__(
        self,
        db: Session,
        user: User,
        model: Optional[str] = None
    ):
        """
        Initialize AI Orchestrator

        Args:
            db: Database session
            user: Current user
            model: OpenAI model to use (defaults to settings)
        """
        self.db = db
        self.user = user
        self.provider = get_llm_provider(model)
        self.company_context = self._fetch_company_context()

    def _fetch_company_context(self) -> Optional[Dict[str, Any]]:
        """Fetch company context for the user"""
        context = (
            self.db.query(CompanyContext)
            .filter(CompanyContext.user_id == self.user.id)
            .first()
        )

        if not context:
            return None

        return {
            "tone": context.tone,
            "company_description": context.company_description,
            "products": context.products or [],
            "policies": context.policies or {},
            "faq": context.faq or [],
            "roles": context.roles or {},
        }

    def _fetch_thread_emails(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all emails in a thread

        Returns:
            List of email dictionaries with sender, timestamp, body
        """
        thread = (
            self.db.query(Thread)
            .filter(Thread.id == thread_id, Thread.user_id == self.user.id)
            .first()
        )

        if not thread:
            raise ValueError(f"Thread {thread_id} not found")

        emails = (
            self.db.query(Email)
            .filter(Email.thread_id == thread_id)
            .order_by(Email.timestamp)
            .all()
        )

        return [
            {
                "sender": email.sender,
                "timestamp": email.timestamp.isoformat(),
                "body": self._clean_email_body(email.body_text_clean),
            }
            for email in emails
        ]

    def _clean_email_body(self, body: str, max_length: int = 5000) -> str:
        """
        Clean and truncate email body

        Args:
            body: Raw email body text
            max_length: Maximum length to keep

        Returns:
            Cleaned email body
        """
        if not body:
            return ""

        # Remove excessive whitespace
        body = " ".join(body.split())

        # Truncate if too long
        if len(body) > max_length:
            body = body[:max_length] + "...[truncated]"

        return body

    def _call_llm_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """
        Call LLM with retry logic

        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to request JSON output

        Returns:
            LLM response

        Raises:
            ExternalServiceError: If all retries fail
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.provider.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode
                )
                return response

            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        # All retries failed
        logger.error(f"LLM call failed after {max_retries} attempts: {str(last_error)}")
        raise ExternalServiceError(
            f"AI service temporarily unavailable: {str(last_error)}"
        )

    def summarize_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Generate AI summary for email thread

        Args:
            thread_id: Thread ID

        Returns:
            Dictionary with summary_text and model_used
        """
        logger.info(f"Generating summary for thread {thread_id}")

        # Fetch thread data
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError("Thread not found")

        emails = self._fetch_thread_emails(thread_id)

        # Build prompt with context injection
        prompt = PromptTemplates.summarization_prompt(
            thread_subject=thread.subject,
            emails=emails,
            company_context=self.company_context
        )

        # Call LLM
        summary = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.5,  # Lower temperature for factual summarization
            max_tokens=200
        )

        return {
            "summary_text": summary.strip(),
            "model_used": self.provider.get_provider_name()
        }

    def classify_priority(self, thread_id: str) -> Dict[str, Any]:
        """
        Classify email thread priority

        Args:
            thread_id: Thread ID

        Returns:
            Dictionary with priority_level, category, reasoning
        """
        logger.info(f"Classifying priority for thread {thread_id}")

        # Fetch thread data
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError("Thread not found")

        emails = self._fetch_thread_emails(thread_id)
        latest_email = emails[-1] if emails else None

        if not latest_email:
            raise ValueError("No emails in thread")

        # Build prompt
        prompt = PromptTemplates.priority_classification_prompt(
            thread_subject=thread.subject,
            latest_email_body=latest_email["body"],
            sender=latest_email["sender"],
            company_context=self.company_context
        )

        # Call LLM with JSON mode
        response = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.3,  # Low temperature for consistent classification
            max_tokens=300,
            json_mode=True
        )

        # Parse JSON response
        result = parse_json_response(response)

        return {
            "priority_level": result.get("priority_level", "low"),
            "category": result.get("category", "general"),
            "reasoning": result.get("reasoning", "")
        }

    def analyze_sentiment(self, thread_id: str) -> Dict[str, Any]:
        """
        Analyze sentiment of email thread

        Args:
            thread_id: Thread ID

        Returns:
            Dictionary with sentiment_score, sentiment_label, anger_level, urgency_score
        """
        logger.info(f"Analyzing sentiment for thread {thread_id}")

        # Fetch thread data
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError("Thread not found")

        emails = self._fetch_thread_emails(thread_id)

        # Build prompt
        prompt = PromptTemplates.sentiment_analysis_prompt(
            thread_subject=thread.subject,
            emails=emails
        )

        # Call LLM with JSON mode
        response = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.3,
            max_tokens=400,
            json_mode=True
        )

        # Parse JSON response
        result = parse_json_response(response)

        return {
            "sentiment_score": float(result.get("sentiment_score", 0.0)),
            "sentiment_label": result.get("sentiment_label", "neutral"),
            "anger_level": float(result.get("anger_level", 0.0)),
            "urgency_score": float(result.get("urgency_score", 0.0)),
            "key_indicators": result.get("key_indicators", [])
        }

    def generate_reply(
        self,
        thread_id: str,
        tone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI reply draft

        Args:
            thread_id: Thread ID
            tone: Desired tone (defaults to company context tone)

        Returns:
            Dictionary with draft_text and tone_used
        """
        logger.info(f"Generating reply for thread {thread_id}")

        # Fetch thread data
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError("Thread not found")

        emails = self._fetch_thread_emails(thread_id)

        # Determine tone
        if tone is None and self.company_context:
            tone = self.company_context.get("tone", "professional and helpful")
        elif tone is None:
            tone = "professional and helpful"

        # Build prompt with full context injection
        prompt = PromptTemplates.reply_generation_prompt(
            thread_subject=thread.subject,
            emails=emails,
            company_context=self.company_context,
            tone=tone
        )

        # Call LLM
        draft = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.7,  # Higher temperature for more natural responses
            max_tokens=140  # Limit to ~100 words
        )

        return {
            "draft_text": draft.strip(),
            "tone_used": tone
        }

    def extract_tasks(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Extract action items and tasks from email thread

        Args:
            thread_id: Thread ID

        Returns:
            List of task dictionaries
        """
        logger.info(f"Extracting tasks from thread {thread_id}")

        # Fetch thread data
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError("Thread not found")

        emails = self._fetch_thread_emails(thread_id)

        # Build prompt
        prompt = PromptTemplates.task_extraction_prompt(
            thread_subject=thread.subject,
            emails=emails,
            company_context=self.company_context
        )

        # Call LLM with JSON mode
        response = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.3,
            max_tokens=800,
            json_mode=True
        )

        # Parse JSON response
        tasks = parse_json_response(response)

        # Ensure it's a list
        if isinstance(tasks, dict) and "tasks" in tasks:
            tasks = tasks["tasks"]
        elif not isinstance(tasks, list):
            tasks = []

        return tasks

    def rewrite_reply(
        self,
        original_draft: str,
        instruction: str
    ) -> str:
        """
        Rewrite a reply draft with different style

        Args:
            original_draft: Original draft text
            instruction: How to rewrite (e.g., "shorter", "more formal")

        Returns:
            Rewritten draft text
        """
        logger.info(f"Rewriting reply with instruction: {instruction}")

        prompt = PromptTemplates.reply_rewrite_prompt(
            original_draft=original_draft,
            rewrite_instruction=instruction
        )

        rewritten = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.7,
            max_tokens=500
        )

        return rewritten.strip()

    def detect_escalation(
        self,
        thread_id: str,
        sentiment_data: Dict[str, Any],
        priority_level: str
    ) -> Dict[str, Any]:
        """
        Detect if thread requires escalation (Slack alert)

        Args:
            thread_id: Thread ID
            sentiment_data: Sentiment analysis results
            priority_level: Priority classification

        Returns:
            Escalation decision with reasoning
        """
        logger.info(f"Detecting escalation for thread {thread_id}")

        # Fetch thread data
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError("Thread not found")

        emails = self._fetch_thread_emails(thread_id)
        latest_email = emails[-1] if emails else None

        if not latest_email:
            raise ValueError("No emails in thread")

        # Build prompt
        prompt = PromptTemplates.escalation_detection_prompt(
            thread_subject=thread.subject,
            latest_email_body=latest_email["body"],
            sentiment_data=sentiment_data,
            priority_level=priority_level
        )

        # Call LLM
        response = self._call_llm_with_retry(
            prompt=prompt,
            temperature=0.2,  # Very low temperature for consistent decisions
            max_tokens=300,
            json_mode=True
        )

        result = parse_json_response(response)

        return {
            "should_escalate": result.get("should_escalate", False),
            "reason": result.get("reason", ""),
            "suggested_owner": result.get("suggested_owner", ""),
            "urgency_level": result.get("urgency_level", "low")
        }
