"""
Redis Client

Provides Redis connection for queuing and caching
"""

import logging
import redis
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client singleton"""

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        """
        Get Redis client instance (singleton)

        Returns:
            Redis client instance
        """
        if cls._instance is None:
            try:
                cls._instance = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                # Test connection
                cls._instance.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise

        return cls._instance

    @classmethod
    def close(cls):
        """Close Redis connection"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")


def get_redis() -> redis.Redis:
    """
    Get Redis client instance

    Usage in dependencies:
        redis_client = get_redis()
    """
    return RedisClient.get_instance()


# Global instance
redis_client = get_redis()
