from redis.asyncio import Redis
from config import settings

redis_client: Redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    username=settings.REDIS_USER,
    password=settings.REDIS_USER_PW,
    decode_responses=True
    )