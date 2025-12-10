"""
Email Parsing Utilities

Functions for parsing, cleaning, and extracting text from emails
"""

import re
import base64
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import html2text

logger = logging.getLogger(__name__)


def decode_base64(data: str) -> str:
    """
    Decode base64 encoded string

    Args:
        data: Base64 encoded string

    Returns:
        Decoded string
    """
    try:
        # Gmail API returns base64url encoded strings
        # Replace URL-safe characters
        data = data.replace('-', '+').replace('_', '/')

        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding

        decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
        return decoded
    except Exception as e:
        logger.warning(f"Failed to decode base64: {str(e)}")
        return data


def clean_html_to_text(html_content: str) -> str:
    """
    Convert HTML email to clean plain text

    Args:
        html_content: HTML content string

    Returns:
        Clean plain text
    """
    try:
        # Use html2text for better formatting preservation
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines

        text = h.handle(html_content)

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        text = text.strip()

        return text
    except Exception as e:
        logger.error(f"HTML to text conversion failed: {str(e)}")
        # Fallback to BeautifulSoup
        return clean_html_simple(html_content)


def clean_html_simple(html_content: str) -> str:
    """
    Simple HTML to text conversion using BeautifulSoup

    Args:
        html_content: HTML content string

    Returns:
        Plain text
    """
    try:
        soup = BeautifulSoup(html_content, 'lxml')

        # Remove script and style elements
        for script in soup(['script', 'style', 'head', 'meta']):
            script.decompose()

        # Get text
        text = soup.get_text(separator='\n')

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = '\n'.join(line for line in lines if line)

        return text
    except Exception as e:
        logger.error(f"Simple HTML cleaning failed: {str(e)}")
        return html_content


def remove_email_signatures(text: str) -> str:
    """
    Attempt to remove email signatures from text

    Args:
        text: Email text content

    Returns:
        Text with signatures removed
    """
    # Common signature markers
    signature_markers = [
        r'\n--\s*\n',  # Standard signature delimiter
        r'\nSent from my iPhone',
        r'\nSent from my Android',
        r'\nGet Outlook for',
        r'\n_{10,}',  # Long underscore lines
    ]

    for marker in signature_markers:
        match = re.search(marker, text, re.IGNORECASE)
        if match:
            text = text[:match.start()]
            break

    return text.strip()


def extract_thread_messages(text: str) -> list:
    """
    Split email thread into individual messages

    Args:
        text: Full thread text

    Returns:
        List of individual message texts
    """
    # Common thread delimiters
    delimiters = [
        r'\n-+ Original Message -+\n',
        r'\nOn .+ wrote:\n',
        r'\nFrom:.+\nSent:.+\nTo:.+\nSubject:.+\n',
    ]

    messages = [text]

    for delimiter in delimiters:
        parts = re.split(delimiter, messages[-1], maxsplit=1)
        if len(parts) > 1:
            messages = parts

    return [msg.strip() for msg in messages if msg.strip()]


def extract_email_metadata(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metadata from email data

    Args:
        email_data: Raw email data from Gmail/Outlook

    Returns:
        Dictionary with normalized metadata
    """
    metadata = {
        'subject': '',
        'from': '',
        'to': [],
        'cc': [],
        'date': None,
        'message_id': '',
        'in_reply_to': '',
        'thread_id': ''
    }

    # Gmail format
    if 'payload' in email_data:
        headers = email_data.get('payload', {}).get('headers', [])
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')

            if name == 'subject':
                metadata['subject'] = value
            elif name == 'from':
                metadata['from'] = value
            elif name == 'to':
                metadata['to'] = [addr.strip() for addr in value.split(',')]
            elif name == 'cc':
                metadata['cc'] = [addr.strip() for addr in value.split(',')]
            elif name == 'date':
                metadata['date'] = value
            elif name == 'message-id':
                metadata['message_id'] = value
            elif name == 'in-reply-to':
                metadata['in_reply_to'] = value

        metadata['thread_id'] = email_data.get('threadId', '')

    # Outlook format
    elif 'subject' in email_data:
        metadata['subject'] = email_data.get('subject', '')

        from_data = email_data.get('from', {}).get('emailAddress', {})
        metadata['from'] = f"{from_data.get('name', '')} <{from_data.get('address', '')}>"

        to_recipients = email_data.get('toRecipients', [])
        metadata['to'] = [
            f"{r.get('emailAddress', {}).get('name', '')} <{r.get('emailAddress', {}).get('address', '')}>"
            for r in to_recipients
        ]

        cc_recipients = email_data.get('ccRecipients', [])
        metadata['cc'] = [
            f"{r.get('emailAddress', {}).get('name', '')} <{r.get('emailAddress', {}).get('address', '')}>"
            for r in cc_recipients
        ]

        metadata['date'] = email_data.get('receivedDateTime', '')
        metadata['message_id'] = email_data.get('internetMessageId', '')
        metadata['thread_id'] = email_data.get('conversationId', '')

    return metadata


def extract_plain_text(email_data: Dict[str, Any]) -> str:
    """
    Extract plain text content from email data

    Args:
        email_data: Raw email data from Gmail/Outlook

    Returns:
        Plain text content
    """
    # Gmail format
    if 'payload' in email_data:
        return extract_gmail_text(email_data['payload'])

    # Outlook format
    elif 'body' in email_data:
        body = email_data.get('body', {})
        content_type = body.get('contentType', 'text')
        content = body.get('content', '')

        if content_type == 'html':
            return clean_html_to_text(content)
        else:
            return content

    return ""


def extract_gmail_text(payload: Dict[str, Any]) -> str:
    """
    Extract text from Gmail payload

    Args:
        payload: Gmail message payload

    Returns:
        Extracted text
    """
    text = ""

    # Check if single part
    if 'body' in payload and payload['body'].get('data'):
        text = decode_base64(payload['body']['data'])

        # If it's HTML, convert to text
        mime_type = payload.get('mimeType', '')
        if 'html' in mime_type.lower():
            text = clean_html_to_text(text)

    # Check if multipart
    elif 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')

            # Recursively extract from parts
            if 'parts' in part:
                text += extract_gmail_text(part)
            elif 'body' in part and part['body'].get('data'):
                part_text = decode_base64(part['body']['data'])

                # Prefer plain text, but use HTML if that's all we have
                if 'text/plain' in mime_type:
                    text += part_text + "\n\n"
                elif 'text/html' in mime_type and not text:
                    text += clean_html_to_text(part_text) + "\n\n"

    return text.strip()


def extract_sender_email(from_string: str) -> str:
    """
    Extract email address from 'From' header

    Args:
        from_string: From header value (e.g., "John Doe <john@example.com>")

    Returns:
        Email address only
    """
    # Try to extract email from angle brackets
    match = re.search(r'<([^>]+)>', from_string)
    if match:
        return match.group(1)

    # If no brackets, assume the whole string is the email
    return from_string.strip()


def truncate_text(text: str, max_length: int = 10000) -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length] + "\n\n...[truncated]"
