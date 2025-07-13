"""
Redis client configuration
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import logging

from .config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            return await self.redis.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            result = await self.redis.set(key, value, ex=expire)
            return result
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis exists failed: {e}")
            return False
    
    async def lpush(self, key: str, *values) -> int:
        """Push values to the left of a list"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
            
            result = await self.redis.lpush(key, *serialized_values)
            return result
        except Exception as e:
            logger.error(f"Redis lpush failed: {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from the right of a list"""
        try:
            value = await self.redis.rpop(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis rpop failed: {e}")
            return None
    
    async def llen(self, key: str) -> int:
        """Get length of a list"""
        try:
            result = await self.redis.llen(key)
            return result
        except Exception as e:
            logger.error(f"Redis llen failed: {e}")
            return 0
    
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to a channel"""
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            
            result = await self.redis.publish(channel, message)
            return result
        except Exception as e:
            logger.error(f"Redis publish failed: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

# Global Redis client instance
redis_client = RedisClient()