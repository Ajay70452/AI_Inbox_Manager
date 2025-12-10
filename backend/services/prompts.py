"""
AI Prompt Templates

This module contains all prompt templates for different AI tasks.
These are the foundation of the AI orchestration layer.
"""

from typing import Dict, Any


class PromptTemplates:
    """Centralized prompt templates for AI processing"""

    @staticmethod
    def summarization_prompt(
        thread_subject: str,
        emails: list,
        company_context: Dict[str, Any] = None
    ) -> str:
        """
        Generate prompt for email thread summarization

        Args:
            thread_subject: Email thread subject
            emails: List of email dictionaries with sender, timestamp, body
            company_context: Optional company context for better understanding

        Returns:
            Formatted prompt string
        """
        # Build email thread text
        thread_text = f"Subject: {thread_subject}\n\n"
        for email in emails:
            thread_text += f"From: {email['sender']}\n"
            thread_text += f"Date: {email['timestamp']}\n"
            thread_text += f"Message:\n{email['body']}\n\n"
            thread_text += "---\n\n"

        # Add company context if available
        context_section = ""
        if company_context:
            context_section = f"""
Company Context:
- Company: {company_context.get('company_description', 'N/A')}
- Products/Services: {', '.join(company_context.get('products', []))}
"""

        prompt = f"""You are an AI assistant helping to summarize email conversations.

{context_section}

Email Thread:
{thread_text}

Task: Provide a concise summary of this email thread in 2-3 sentences (max 120 words).

Requirements:
- Focus on key points and action items
- Identify the main topic or issue
- Note any decisions made or pending
- Use clear, professional language

Summary:"""

        return prompt

    @staticmethod
    def priority_classification_prompt(
        thread_subject: str,
        latest_email_body: str,
        sender: str,
        company_context: Dict[str, Any] = None
    ) -> str:
        """
        Generate prompt for priority classification

        Returns priority level and category
        """
        context_section = ""
        if company_context:
            roles = company_context.get('roles', {})
            context_section = f"""
Company Context:
- Known team roles: {', '.join(roles.keys())}
- Products: {', '.join(company_context.get('products', []))}
"""

        prompt = f"""You are an AI assistant that classifies email priority for a business inbox.

{context_section}

Email:
Subject: {thread_subject}
From: {sender}
Body:
{latest_email_body}

Task: Classify this email's priority and category.

Priority Levels:
- urgent: Requires immediate attention (angry customer, system down, legal issue, executive request)
- customer: Customer inquiry or support request (not urgent)
- vendor: Communication from vendors/partners
- internal: Internal team communication
- low: Newsletters, updates, non-critical information

Output as JSON:
{{
    "priority_level": "urgent|customer|vendor|internal|low",
    "category": "brief category description (e.g., 'customer complaint', 'billing inquiry', 'sales lead')",
    "reasoning": "brief explanation for the classification"
}}"""

        return prompt

    @staticmethod
    def sentiment_analysis_prompt(
        thread_subject: str,
        emails: list
    ) -> str:
        """
        Generate prompt for sentiment analysis

        Returns sentiment score, label, anger level, urgency score
        """
        # Build thread text
        thread_text = f"Subject: {thread_subject}\n\n"
        for email in emails:
            thread_text += f"From: {email['sender']}:\n{email['body']}\n\n"

        prompt = f"""You are an AI assistant specialized in analyzing the emotional tone of email conversations.

Email Thread:
{thread_text}

Task: Analyze the sentiment and emotional tone of this email conversation.

Output as JSON:
{{
    "sentiment_score": <float between -1.0 (very negative) and 1.0 (very positive)>,
    "sentiment_label": "positive|neutral|negative",
    "anger_level": <float between 0.0 (calm) and 1.0 (very angry)>,
    "urgency_score": <float between 0.0 (not urgent) and 1.0 (extremely urgent)>,
    "key_indicators": ["list of phrases or words that indicate the sentiment"]
}}

Consider:
- Tone and language used
- Presence of complaints, frustration, or appreciation
- Time-sensitive language
- ALL CAPS, exclamation marks, aggressive wording"""

        return prompt

    @staticmethod
    def reply_generation_prompt(
        thread_subject: str,
        emails: list,
        company_context: Dict[str, Any] = None,
        tone: str = "professional and helpful"
    ) -> str:
        """
        Generate prompt for auto-reply drafting

        Args:
            thread_subject: Email subject
            emails: Email history
            company_context: Company policies, FAQs, tone guidelines
            tone: Desired tone (professional, friendly, formal, concise)

        Returns:
            Draft reply
        """
        # Build conversation history
        conversation = f"Subject: {thread_subject}\n\n"
        for email in emails:
            conversation += f"From: {email['sender']}:\n{email['body']}\n\n---\n\n"

        # Build company context section
        context_section = ""
        if company_context:
            context_section = f"""
Company Information:
- Company: {company_context.get('company_description', '')}
- Products/Services: {', '.join(company_context.get('products', []))}
- Tone Guidelines: {company_context.get('tone', 'professional and helpful')}

Company Policies:
{company_context.get('policies', {})}

Frequently Asked Questions:
{company_context.get('faq', [])}

Team Roles:
{company_context.get('roles', {})}
"""

        prompt = f"""You are an AI email assistant helping to draft professional email responses.

{context_section}

Email Conversation:
{conversation}

Task: Draft a reply to the most recent email in this thread.

Requirements:
- Tone: {tone}
- Address the sender's questions or concerns directly
- Use company policies and FAQ information when relevant
- Keep the reply VERY SHORT and concise (maximum 100 words)
- Use proper email etiquette
- Do NOT include subject line, greetings like "Dear", or closing signatures
- Start directly with the response content

Draft Reply:"""

        return prompt

    @staticmethod
    def task_extraction_prompt(
        thread_subject: str,
        emails: list,
        company_context: Dict[str, Any] = None
    ) -> str:
        """
        Generate prompt for extracting action items and tasks

        Returns list of tasks with title, description, due date, owner
        """
        # Build thread text
        thread_text = f"Subject: {thread_subject}\n\n"
        for email in emails:
            thread_text += f"From: {email['sender']}:\n{email['body']}\n\n---\n\n"

        roles_info = ""
        if company_context and company_context.get('roles'):
            roles_info = f"\nKnown team roles: {', '.join(company_context['roles'].keys())}"

        prompt = f"""You are an AI assistant that extracts action items and tasks from email conversations.

{roles_info}

Email Thread:
{thread_text}

Task: Extract all action items, tasks, and deliverables mentioned in this email thread.

Output as JSON array:
[
    {{
        "title": "brief task title",
        "description": "detailed task description",
        "due_date": "YYYY-MM-DD or null if not mentioned",
        "extracted_owner": "person or role responsible (or null if not clear)",
        "priority": "high|medium|low"
    }}
]

Rules:
- Only extract explicit action items (things that need to be done)
- Ignore completed tasks or past events
- Extract realistic due dates mentioned in the emails
- If no tasks are found, return an empty array []
- Be conservative - don't hallucinate tasks that aren't clearly stated"""

        return prompt

    @staticmethod
    def escalation_detection_prompt(
        thread_subject: str,
        latest_email_body: str,
        sentiment_data: Dict[str, Any],
        priority_level: str
    ) -> str:
        """
        Generate prompt for escalation detection

        Determines if email should trigger Slack alert
        """
        prompt = f"""You are an AI assistant that determines if an email requires immediate escalation to the team.

Email:
Subject: {thread_subject}
Body: {latest_email_body}

Context:
- Priority: {priority_level}
- Sentiment: {sentiment_data.get('sentiment_label')}
- Anger Level: {sentiment_data.get('anger_level')}
- Urgency Score: {sentiment_data.get('urgency_score')}

Task: Determine if this email should trigger an immediate alert to the team (via Slack).

Escalation Criteria:
- Very angry or frustrated customer
- Urgent issue affecting service
- Legal or compliance matter
- Executive-level communication
- SLA breach or imminent breach
- Security incident

Output as JSON:
{{
    "should_escalate": true|false,
    "reason": "brief explanation",
    "suggested_owner": "which team member or role should handle this",
    "urgency_level": "critical|high|medium|low"
}}"""

        return prompt

    @staticmethod
    def reply_rewrite_prompt(
        original_draft: str,
        rewrite_instruction: str
    ) -> str:
        """
        Generate prompt for rewriting reply with different style

        Args:
            original_draft: The original draft reply
            rewrite_instruction: How to rewrite (e.g., "shorter", "more formal", "friendlier")

        Returns:
            Rewritten reply
        """
        prompt = f"""You are an AI assistant that rewrites email drafts with different styles.

Original Draft:
{original_draft}

Task: Rewrite this draft to be {rewrite_instruction}.

Requirements:
- Maintain the core message and information
- Apply the requested style change
- Keep it professional
- Do NOT add subject line or closing signature
- Return only the rewritten body text

Rewritten Draft:"""

        return prompt
