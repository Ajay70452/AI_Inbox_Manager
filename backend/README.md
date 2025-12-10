# AI Inbox Manager - Backend API

FastAPI backend for AI-powered email management system.

## Features

- 🔐 **Authentication**: JWT-based auth with OAuth2 for Gmail & Outlook
- 📧 **Email Sync**: Incremental email syncing from Gmail & Outlook
- 🤖 **AI Processing**: Email summarization, priority classification, sentiment analysis, auto-replies, task extraction
- 🔗 **Integrations**: Slack, ClickUp, Notion, Jira, Trello
- 📊 **Company Context**: Customizable AI behavior based on company policies
- 🗄️ **Database**: PostgreSQL with SQLAlchemy ORM
- 🔄 **Background Jobs**: Redis-based task queue

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis 7+
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (python-jose)
- **LLM API**: OpenAI (GPT-4)
- **OAuth**: Google OAuth2, Microsoft Graph

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate to project**:
   ```bash
   cd "F:\Startups\AI Inbox Manager"
   ```

2. **Create `.env` file**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

3. **Start all services**:
   ```bash
   cd ..
   docker-compose up -d
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

### Option 2: Local Development

1. **Create virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start PostgreSQL and Redis** (if not using Docker):
   ```bash
   # Using Docker for just DB and Redis:
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15-alpine
   docker run -d -p 6379:6379 redis:7-alpine
   ```

5. **Initialize database**:
   ```bash
   python -m db.init_db
   ```

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Project Structure

```
backend/
├── app/                    # FastAPI application
│   ├── main.py            # Entry point
│   ├── config.py          # Settings
│   ├── dependencies.py    # Shared dependencies
│   └── middleware.py      # Middleware configuration
├── routers/               # API endpoints
│   ├── auth.py           # Authentication
│   ├── users.py          # User management
│   ├── emails.py         # Email operations
│   ├── threads.py        # Thread operations
│   ├── context.py        # Company context
│   ├── ai.py             # AI processing
│   └── integrations.py   # External integrations
├── services/             # Business logic
├── workers/              # Background jobs (see WORKERS_IMPLEMENTATION.md)
├── cli/                  # CLI commands for worker management
├── models/               # SQLAlchemy models
├── schemas/              # Pydantic schemas
├── core/                 # Core utilities (auth, security)
├── db/                   # Database configuration
├── utils/                # Helper functions
└── tests/                # Test suite
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/google/start` - Start Gmail OAuth
- `GET /api/v1/auth/google/callback` - Gmail OAuth callback
- `GET /api/v1/auth/outlook/start` - Start Outlook OAuth
- `GET /api/v1/auth/outlook/callback` - Outlook OAuth callback

### User Management
- `GET /api/v1/user/profile` - Get user profile
- `PUT /api/v1/user/profile` - Update profile
- `PUT /api/v1/user/password` - Change password
- `DELETE /api/v1/user` - Delete account

### Emails & Threads
- `POST /api/v1/emails/sync` - Trigger email sync
- `GET /api/v1/emails/{email_id}` - Get email
- `GET /api/v1/threads` - List threads (with filters)
- `GET /api/v1/threads/{thread_id}` - Get thread details

### AI Processing
- `POST /api/v1/ai/summarize` - Generate thread summary
- `POST /api/v1/ai/classify` - Classify priority
- `POST /api/v1/ai/sentiment` - Analyze sentiment
- `POST /api/v1/ai/reply` - Generate auto-reply
- `POST /api/v1/ai/tasks/extract` - Extract tasks

### Company Context
- `GET /api/v1/context` - Get company context
- `PUT /api/v1/context` - Update company context
- `DELETE /api/v1/context/{section}` - Delete context section

### Integrations
- `GET /api/v1/integrations` - List integrations
- `GET /api/v1/integrations/slack/start` - Connect Slack
- `POST /api/v1/integrations/slack/alert` - Send Slack alert
- `GET /api/v1/integrations/{tool}/start` - Connect tool (Notion, ClickUp, etc.)
- `POST /api/v1/integrations/{tool}/task` - Create task in tool

### Background Workers
- `POST /api/v1/workers/sync/trigger` - Trigger email sync
- `POST /api/v1/workers/ai/process/trigger` - Trigger AI processing
- `GET /api/v1/workers/scheduler/status` - Get scheduler status
- `POST /api/v1/workers/scheduler/{job_id}/pause` - Pause job
- `POST /api/v1/workers/scheduler/{job_id}/resume` - Resume job
- `GET /api/v1/workers/monitor/stats` - Get worker statistics
- `GET /api/v1/workers/monitor/{worker_name}/history` - Get execution history
- `GET /api/v1/workers/monitor/failures` - Get recent failures

See [WORKERS_IMPLEMENTATION.md](WORKERS_IMPLEMENTATION.md) for detailed documentation.

## Environment Variables

See `.env.example` for all required environment variables. Key variables:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_inbox_manager

# JWT
SECRET_KEY=your-secret-key-change-this

# OpenAI API
OPENAI_API_KEY=sk-...

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
```

## Database Schema

The application uses PostgreSQL with the following main tables:
- `users` - User accounts
- `account_tokens` - OAuth tokens (encrypted)
- `threads` - Email threads
- `emails` - Individual emails
- `ai_thread_summary` - AI-generated summaries
- `ai_priority` - Priority classifications
- `ai_sentiment` - Sentiment analysis
- `tasks` - Extracted tasks
- `ai_reply_draft` - Auto-reply drafts
- `company_context` - Company-specific AI context
- `integrations` - External service connections
- `sync_job_logs` - Sync operation logs

## Development

### Running Tests
```bash
pytest
pytest --cov=app tests/  # With coverage
```

### Code Formatting
```bash
black .
flake8
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Background Workers

The system includes a comprehensive background worker system for asynchronous tasks. See [WORKERS_IMPLEMENTATION.md](WORKERS_IMPLEMENTATION.md) for full documentation.

### CLI Commands
```bash
# Start scheduler
python -m cli.main worker scheduler start

# Show worker statistics
python -m cli.main worker monitor stats

# Trigger email sync
python -m cli.main worker sync user --user-id <user-id> --lookback-days 7

# Process thread with AI
python -m cli.main worker ai thread --user-id <user-id> --thread-id <thread-id>
```

### Scheduled Jobs
- **Email Sync**: Every 5 minutes (configurable)
- **AI Processing**: Every 10 minutes (configurable)
- **Nightly Cleanup**: 2 AM UTC daily

## Next Steps

### Implementation Status
1. ✅ Core authentication and user management
2. ✅ Gmail OAuth integration service
3. ✅ Outlook OAuth integration service
4. ✅ Email sync service (incremental fetch)
5. ✅ AI orchestration layer (context injection)
6. ✅ LLM processing services (OpenAI, Claude, Gemini)
7. ✅ Background workers (email sync, AI processing)
8. ⏳ Slack integration
9. ⏳ ClickUp, Notion, Jira, Trello integrations
10. ⏳ Chrome extension API support
11. ⏳ Frontend web dashboard

## License

Proprietary - All rights reserved
