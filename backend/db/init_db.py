from sqlalchemy import inspect
from models import Base
from db.session import engine
import logging

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def check_db_connection():
    """Check if database connection is working"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Database connection successful. Found {len(tables)} tables.")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing database...")
    init_db()
    check_db_connection()
