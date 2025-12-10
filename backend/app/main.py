from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.middleware import setup_middleware
from db import check_db_connection, init_db
from routers import auth, users, emails, threads, context, ai, integrations, workers
from workers import start_scheduler, stop_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting AI Inbox Manager API...")
    logger.info(f"Environment: {settings.ENV}")

    # Check database connection
    if not check_db_connection():
        logger.error("Failed to connect to database")
    else:
        logger.info("Database connection established")
        # Initialize database tables if needed
        if settings.ENV == "development":
            init_db()

    # Start background worker scheduler
    try:
        start_scheduler()
        logger.info("Background worker scheduler started")
    except Exception as e:
        logger.error(f"Failed to start worker scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down AI Inbox Manager API...")

    # Stop background worker scheduler
    try:
        stop_scheduler()
        logger.info("Background worker scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop worker scheduler: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered email management for Gmail & Outlook",
    lifespan=lifespan,
    docs_url=f"{settings.API_BASE_URL}/docs",
    redoc_url=f"{settings.API_BASE_URL}/redoc",
    openapi_url=f"{settings.API_BASE_URL}/openapi.json",
)

# Setup middleware
setup_middleware(app)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Validation error",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_BASE_URL}/docs",
    }


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_BASE_URL}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_BASE_URL}/user", tags=["Users"])
app.include_router(emails.router, prefix=f"{settings.API_BASE_URL}/emails", tags=["Emails"])
app.include_router(threads.router, prefix=f"{settings.API_BASE_URL}/threads", tags=["Threads"])
app.include_router(context.router, prefix=f"{settings.API_BASE_URL}/context", tags=["Company Context"])
app.include_router(ai.router, prefix=f"{settings.API_BASE_URL}/ai", tags=["AI Processing"])
app.include_router(integrations.router, prefix=f"{settings.API_BASE_URL}/integrations", tags=["Integrations"])
app.include_router(workers.router, prefix=f"{settings.API_BASE_URL}/workers", tags=["Background Workers"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
