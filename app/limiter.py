from fastapi import Request, HTTPException
from app import cache
import time
 
 
async def rate_limit(request: Request):
    ip = request.client.host
    key = f"rate:{ip}:{int(time.time() // 60)}"  # new bucket every minute
 
    count = await cache.redis.incr(key)
    if count == 1:
        await cache.redis.expire(key, 60)  # expire bucket after 60 seconds
 
    if count > 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")