# 🤖 AI Inbox Manager

AI-powered email management system for Gmail & Outlook with smart summaries, auto-replies, priority classification, and productivity integrations.

## 🎯 Overview

AI Inbox Manager transforms email chaos into actionable workflows with:

- **AI Summarization**: Get concise summaries of long email threads
- **Priority Classification**: Auto-categorize emails (urgent, customer, vendor, internal, low)
- **Sentiment Analysis**: Detect angry/frustrated customers and escalate automatically
- **Auto-Reply Drafts**: Generate context-aware responses based on company policies
- **Task Extraction**: Pull action items, deadlines, and deliverables from emails
- **Smart Integrations**: Push to Slack, ClickUp, Notion, Jira, Trello

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Chrome Extension                            │
│              (Gmail/Outlook Sidebar UI)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Auth Service │  │ Email Sync   │  │ AI Orchestration│       │
│  │ (OAuth2/JWT) │  │ (Incremental)│  │ (Context Inject)│       │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │LLM Processing│  │ Integrations │  │ Company Context│        │
│  │(OpenAI/Claude│  │ (Slack, etc.)│  │ Engine         │        │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Data Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ PostgreSQL   │  │ Redis Queue  │  │ S3/R2 Storage│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- API Keys: OpenAI, Google OAuth, Microsoft OAuth

### 1. Clone and Setup

```bash
cd "F:\Startups\AI Inbox Manager"
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Start Services

```bash
cd ..
docker-compose up -d
```

### 4. Access the Application

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

## 📦 Project Structure

```
AI Inbox Manager/
├── backend/                    # FastAPI backend
│   ├── app/                   # Application core
│   ├── routers/               # API endpoints
│   ├── services/              # Business logic
│   ├── models/                # Database models
│   ├── schemas/               # Pydantic schemas
│   ├── core/                  # Security & utilities
│   ├── db/                    # Database config
│   ├── workers/               # Background jobs
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Web dashboard (Next.js) - TODO
├── extension/                  # Chrome extension - TODO
├── docker-compose.yml         # Docker services
└── README.md                  # This file
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis 7+
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT + OAuth2

### AI & Integrations
- **LLMs**: OpenAI GPT-4, Anthropic Claude, Google Gemini
- **Email**: Gmail API, Microsoft Graph API
- **Integrations**: Slack, ClickUp, Notion, Jira, Trello

### Frontend (Coming Soon)
- **Web App**: Next.js 14, React, TypeScript
- **Extension**: React + Vite, Chrome Extension API
- **State**: Zustand + React Query

## 📚 Documentation

- [Backend API Documentation](./backend/README.md)
- [AI Orchestration Layer](./AI_ORCHESTRATION_IMPLEMENTATION.md) 🌟
- [Email Sync Service](./EMAIL_SYNC_IMPLEMENTATION.md) 🌟 **NEW!**
- [AI Services README](./backend/services/README.md)
- [Product Requirements](./PRODUCT%20REQUIREMENT%20DOCUMENT.docx)
- [Architecture Diagram](./📐%20ARCHITECTURE%20DIAGRAM.txt)
- [Database Schema](./Database%20schema.docx)
- [API Endpoints Specification](./Backend%20API%20Endpoints%20Specification.docx)

## 🔧 Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn app.main:app --reload
```

### Testing

```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

## 🗺️ Roadmap

### Phase 1: Core Backend ✅ **COMPLETE**
- [x] FastAPI application structure
- [x] PostgreSQL database models (12 tables)
- [x] Authentication (JWT + OAuth placeholders)
- [x] API endpoints structure (7 routers)
- [x] Docker Compose setup
- [x] **AI orchestration layer** 🌟 **NEW!**
- [x] **LLM processing services** 🌟 **NEW!**
- [x] **Multi-provider support** (OpenAI, Claude, Gemini) 🌟 **NEW!**

### Phase 1.5: AI Features ✅ **COMPLETE** 🎉
- [x] **Email summarization** - Context-aware thread summaries
- [x] **Priority classification** - 5-level priority system
- [x] **Sentiment analysis** - Emotion + urgency detection
- [x] **Auto-reply generation** - Company policy-aware drafts
- [x] **Task extraction** - Action items with deadlines
- [x] **Company context injection** - The "secret sauce"
- [x] **Reply rewriting** - Style transformations

### Phase 2: Email Integration ✅ **COMPLETE** 🎉
- [x] **Gmail OAuth integration** - Full OAuth 2.0 flow
- [x] **Outlook OAuth integration** - Microsoft Graph OAuth
- [x] **Email sync service** - Incremental sync for both providers
- [x] **Email parsing** - HTML to text, metadata extraction
- [x] **S3/R2 storage** - HTML content and attachments
- [x] **Sync orchestration** - Multi-provider coordination
- [x] **API endpoints** - Sync, status, OAuth callbacks

### Phase 3: Background Processing (Next)
- [ ] Background workers (Celery/RQ)
- [ ] Cron jobs for automatic sync
- [ ] Webhook handling (Gmail push, Outlook subscriptions)
- [ ] Automatic AI processing pipeline

### Phase 4: Integrations
- [ ] Slack alerts
- [ ] ClickUp tasks
- [ ] Notion updates
- [ ] Jira issues
- [ ] Trello cards

### Phase 4: Frontend
- [ ] Web dashboard (Next.js)
- [ ] Chrome extension
- [ ] User onboarding flow
- [ ] Analytics dashboard

### Phase 5: Advanced Features
- [ ] Team collaboration
- [ ] Shared inboxes
- [ ] Advanced analytics
- [ ] Custom automation rules

## 🔐 Security

- JWT-based authentication
- OAuth2 for Gmail/Outlook
- Encrypted token storage (Fernet)
- CORS protection
- Rate limiting (Redis)
- SQL injection protection (SQLAlchemy ORM)

## 📄 License

Proprietary - All rights reserved

## 👤 Author

**Ajay Raval**
AI Inbox Manager - Intelligent Email Management Platform

---

**Status**: 🚀 Phase 1 + Phase 2 Complete! Core platform is functional. Next: Background Workers
