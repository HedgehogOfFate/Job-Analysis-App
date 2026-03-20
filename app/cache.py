import json
import logging
import redis.asyncio as redis
from typing import Optional, Any
from . import config

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        try:
            self._client = redis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._client.ping()
            logger.info(f"Connected to Redis at {config.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis unavailable — caching disabled: {e}")
            self._client = None

    async def close(self):
        if self._client:
            await self._client.aclose()
            logger.info("Redis connection closed")

    @property
    def available(self) -> bool:
        return self._client is not None

    async def get(self, key: str) -> Optional[Any]:
        if not self.available:
            return None
        try:
            value = await self._client.get(key)
            if value:
                logger.info(f"Cache HIT: {key}")
                return json.loads(value)
            logger.info(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Redis GET error for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        if not self.available:
            return False
        try:
            serialized = json.dumps(value)
            await self._client.set(key, serialized, ex=ttl or config.REDIS_TTL)
            logger.info(f"Cache SET: {key} (TTL={ttl or config.REDIS_TTL}s)")
            return True
        except Exception as e:
            logger.warning(f"Redis SET error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE error for key '{key}': {e}")
            return False


def make_search_cache_key(what: str, where: str, country: str) -> str:
    return f"search:{what.strip().lower()}:{where.strip().lower()}:{country.strip().lower()}"


cache = RedisCache()