from redis.asyncio import Redis
from config import settings

redis_client: Redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
