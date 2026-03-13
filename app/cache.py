import redis.asyncio as aioredis
import os
 
redis = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
 
 
async def get(key: str):
    value = await redis.get(key)
    return value.decode("utf-8") if value else None
 
 
async def set(key: str, value: str, ttl: int = 3600):
    await redis.set(key, value, ex=ttl)