# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Inbox Manager is an intelligent email management system that integrates with Gmail and Outlook to provide AI-powered summaries, auto-replies, task extraction, and priority classification. The system includes a Chrome extension for in-email UI, a web dashboard, and integrations with productivity tools (Slack, ClickUp, Notion, Jira, Trello).

## Architecture Overview

The system follows a microservices architecture with these major components:

### Frontend Layer

- **Chrome Extension**: Injects sidebar in Gmail/Outlook showing AI summaries, priority labels, sentiment alerts, auto-reply drafts, and extracted tasks
- **Web Dashboard** (React/Next.js): Company context setup, integration settings, email summaries, token management, admin panel, analytics

### Backend Services

- **Authentication Service**: OAuth flows for Gmail/Outlook, token refresh, encrypted token storage in Token Vault
- **Email Sync Service**: Incremental email fetching via Gmail API/Microsoft Graph, webhook-based updates, thread normalization, queues AI processing tasks
- **AI Orchestration Layer**: Routes prompts, injects company context and historical data, manages rate limiting, ensures structured output
- **LLM Processing Service**: Handles summgo tharization, sentiment/urgency detection, priority classification, task extraction, auto-reply generation (uses OpenAI, Claude, Gemini)
- **Integrations Service**: Modular handlers for Slack alerts, ClickUp tasks, Notion updates, Jira issues, Trello cards
- **Company Context Engine**: Stores and provides policies, FAQs, tone guidelines, product info, role definitions

### Data Layer

- **PostgreSQL**: Users, email threads, summaries, company context, task metadata, AI logs
- **Redis**: Background job queue, rate limiting, caching
- **Blob Storage** (S3/GCS/Supabase): Raw HTML email content, attachments, AI logs

## High-Level Flow

1. User authenticates with Gmail/Outlook via OAuth
2. Email Sync Service fetches emails incrementally (webhooks + cron)
3. New emails trigger AI processing pipeline:
   - Thread summarization
   - Priority classification
   - Sentiment analysis
   - Task extraction
   - Auto-reply draft generation
   - Escalation detection
4. Results stored in PostgreSQL
5. Chrome extension displays AI outputs inline in Gmail/Outlook
6. Escalations sent to Slack
7. Tasks pushed to configured productivity tools

## Key Design Principles

- **Modular Integrations**: Each external service (Slack, ClickUp, etc.) is isolated in the Integrations Service
- **Context Injection**: The AI Orchestration Layer is the "secret sauce" that enriches prompts with company context and historical data
- **Incremental Sync**: Email fetching uses webhooks and incremental updates to minimize API calls
- **Secure Token Storage**: OAuth tokens encrypted in dedicated Token Vault
- **Queue-Based Processing**: Redis queues handle async AI tasks and integration actions
- **Lightweight Extension**: Chrome extension contains minimal logic, delegates to backend API

## Development Setup

This repository currently contains specification documents. When implementation begins:

- Backend services will likely use Node.js/Python/FastAPI
- Frontend will use React/Next.js
- Chrome extension will be JavaScript-based
- Database will be PostgreSQL with Redis for queuing

Refer to the specification documents for detailed requirements:

- `📐 ARCHITECTURE DIAGRAM.txt` - System architecture
- `PRODUCT REQUIREMENT DOCUMENT.docx` - Product requirements
- `Backend Folder Structure Document.docx` - Backend organization
- `Backend API Endpoints Specification.docx` - API contracts
- `Database schema.docx` - Data models
- `Front end structure and Guidelines.docx` - Frontend patterns
