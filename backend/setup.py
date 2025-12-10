#!/usr/bin/env python
"""
Setup script to initialize the AI Inbox Manager backend
This script checks dependencies, database connection, and initializes tables
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_env_file():
    """Check if .env file exists"""
    print("\n📝 Checking .env file...")
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Please copy .env.example to .env and configure it")
        return False
    print("✅ .env file found")
    return True


def check_docker_services():
    """Check if Docker services are running"""
    print("\n🐳 Checking Docker services...")

    # Check PostgreSQL
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=ai_inbox_postgres", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            check=True
        )
        if "Up" in result.stdout:
            print("✅ PostgreSQL container is running")
        else:
            print("❌ PostgreSQL container is not running")
            print("   Run: docker-compose up -d postgres")
            return False
    except Exception as e:
        print(f"❌ Could not check PostgreSQL: {e}")
        print("   Make sure Docker is running and containers are started")
        return False

    # Check Redis
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=ai_inbox_redis", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            check=True
        )
        if "Up" in result.stdout:
            print("✅ Redis container is running")
        else:
            print("❌ Redis container is not running")
            print("   Run: docker-compose up -d redis")
            return False
    except Exception as e:
        print(f"❌ Could not check Redis: {e}")
        return False

    return True


def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    try:
        from db.session import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False


def test_redis_connection():
    """Test Redis connection"""
    print("\n📦 Testing Redis connection...")
    try:
        from core.redis_client import get_redis_client

        redis_client = get_redis_client()
        redis_client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running and REDIS_URL is correct")
        return False


def initialize_database():
    """Initialize database tables"""
    print("\n🔨 Initializing database tables...")
    try:
        from db.init_db import init_db

        init_db()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def check_openai_key():
    """Check if OpenAI API key is configured"""
    print("\n🤖 Checking OpenAI API key...")
    try:
        from app.config import settings

        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your-"):
            print("✅ OpenAI API key configured")
            return True
        else:
            print("⚠️  OpenAI API key not configured")
            print("   Add OPENAI_API_KEY to .env file to use AI features")
            return False
    except Exception as e:
        print(f"❌ Could not check OpenAI key: {e}")
        return False


def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 AI Inbox Manager - Backend Setup")
    print("=" * 60)

    checks = []

    # Check Python version
    checks.append(("Python Version", check_python_version()))

    # Check .env file
    checks.append((".env File", check_env_file()))

    # Check Docker services
    docker_running = check_docker_services()
    checks.append(("Docker Services", docker_running))

    if docker_running:
        # Test database connection
        checks.append(("Database Connection", test_database_connection()))

        # Test Redis connection
        checks.append(("Redis Connection", test_redis_connection()))

        # Initialize database
        checks.append(("Database Initialization", initialize_database()))

    # Check OpenAI key (optional)
    check_openai_key()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Setup Summary")
    print("=" * 60)

    for check_name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {check_name}")

    all_passed = all(status for _, status in checks)

    if all_passed:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the server: python app/main.py")
        print("2. Open API docs: http://localhost:8000/api/v1/docs")
        print("3. Test the health endpoint: http://localhost:8000/health")
    else:
        print("\n⚠️  Setup incomplete. Please fix the issues above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
