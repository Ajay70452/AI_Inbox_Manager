# AI Inbox Manager - Setup Guide

## ✅ Completed Steps

### 1. Python Environment
- ✅ Python 3.11.5 installed and verified
- ✅ Virtual environment created at `backend/venv`
- ✅ All Python dependencies installed (FastAPI, SQLAlchemy, Redis, etc.)

### 2. Environment Configuration
- ✅ `.env` file configured with basic settings
- ✅ OpenAI API key configured
- ✅ Database and Redis URLs set for local development

## 🚧 Next Steps (Waiting for Docker)

### 3. Start Docker Services

Once Docker Desktop is ready, run:

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker ps

# Check logs if needed
docker-compose logs postgres
docker-compose logs redis
```

### 4. Initialize Database Schema

After Docker services are running:

```bash
cd backend

# Activate virtual environment
venv\Scripts\activate

# Run database initialization
venv/Scripts/python -c "from db.init_db import init_db; init_db()"

# OR use Alembic migrations (recommended for production)
alembic upgrade head
```

### 5. Start FastAPI Backend

```bash
cd backend

# Make sure virtual environment is activated
venv\Scripts\activate

# Start the server
venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or simply:

```bash
cd backend
venv/Scripts/python app/main.py
```

### 6. Test the API

Once the server is running, access:

- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## 📋 Quick Command Reference

### Virtual Environment Commands

```bash
# Activate (Windows)
cd backend
venv\Scripts\activate

# Deactivate
deactivate

# Install new dependencies
pip install package-name
pip freeze > requirements.txt
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Database Commands

```bash
# Check PostgreSQL connection
docker exec -it ai_inbox_postgres psql -U postgres -d ai_inbox_manager

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Redis Commands

```bash
# Connect to Redis CLI
docker exec -it ai_inbox_redis redis-cli

# Test Redis
docker exec -it ai_inbox_redis redis-cli ping
```

## 🔑 API Keys & OAuth Setup

### Current Status

✅ **Configured:**
- OpenAI API Key

⚠️ **To Configure Later:**

#### Google OAuth (Gmail Integration)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
6. Update `.env` with `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

#### Microsoft OAuth (Outlook Integration)
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new app in Azure AD
3. Add redirect URI: `http://localhost:8000/api/v1/auth/outlook/callback`
4. Grant Microsoft Graph API permissions (Mail.Read, Mail.ReadWrite)
5. Update `.env` with `MICROSOFT_CLIENT_ID` and `MICROSOFT_CLIENT_SECRET`

#### AWS S3 (Email Storage)
1. Create an S3 bucket or CloudFlare R2 bucket
2. Create IAM user with S3 access
3. Update `.env` with AWS credentials

#### Optional Integrations
- **Slack**: Create Slack app and get OAuth credentials
- **ClickUp**: Register OAuth app at ClickUp
- **Notion**: Create Notion integration
- **Jira**: Register Jira app
- **Trello**: Get API keys from Trello Power-Ups

## 🧪 Testing the Setup

### 1. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "AI Inbox Manager",
  "version": "1.0.0",
  "environment": "development"
}
```

### 2. Test AI Summarization (without email sync)

```bash
curl -X POST http://localhost:8000/api/v1/ai/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "test-thread",
    "emails": [
      {
        "subject": "Project Update",
        "body": "Hi team, wanted to update you on the Q4 roadmap...",
        "from": "john@example.com",
        "timestamp": "2024-01-15T10:00:00Z"
      }
    ]
  }'
```

### 3. Run Unit Tests

```bash
cd backend
venv/Scripts/activate
pytest
pytest --cov=app tests/
```

## 📁 Project Structure

```
AI Inbox Manager/
├── backend/
│   ├── venv/                    ✅ Virtual environment
│   ├── app/
│   │   ├── main.py             ✅ FastAPI application
│   │   ├── config.py           ✅ Settings configuration
│   │   └── ...
│   ├── models/                 ✅ Database models
│   ├── routers/                ✅ API endpoints
│   ├── services/               ✅ Business logic
│   ├── workers/                ✅ Background jobs
│   ├── .env                    ✅ Environment variables
│   └── requirements.txt        ✅ Dependencies
├── chrome-extension/           ⚠️ Needs testing
├── docker-compose.yml          ✅ Docker configuration
└── README.md                   ✅ Documentation
```

## 🐛 Troubleshooting

### Docker Issues

**Problem**: Can't connect to Docker daemon
```bash
# Solution: Make sure Docker Desktop is running
```

**Problem**: Port already in use
```bash
# Solution: Change ports in docker-compose.yml or stop conflicting services
netstat -ano | findstr :5432
netstat -ano | findstr :6379
```

### Database Issues

**Problem**: Connection refused
```bash
# Solution: Check if PostgreSQL container is running
docker ps
docker-compose logs postgres
```

**Problem**: Database doesn't exist
```bash
# Solution: Recreate containers
docker-compose down
docker-compose up -d postgres redis
```

### Python Issues

**Problem**: Module not found
```bash
# Solution: Activate virtual environment and reinstall
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

**Problem**: Import errors
```bash
# Solution: Run from the correct directory
cd backend
venv/Scripts/python -m uvicorn app.main:app --reload
```

## 🎯 What's Next?

After setup is complete, you can:

1. **Test AI Features**: Use the `/api/v1/ai/*` endpoints to test summarization, classification, etc.
2. **Set up OAuth**: Configure Google/Microsoft OAuth for email sync
3. **Test Chrome Extension**: Load the extension in Chrome and test with Gmail/Outlook
4. **Configure Integrations**: Set up Slack, ClickUp, Notion, etc.
5. **Deploy**: Set up production environment

## 📞 Need Help?

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Check FastAPI logs in the terminal
3. Review this guide
4. Check the main README.md for architecture details

---

**Ready to continue?** Let me know once Docker is running and we'll complete the setup!
