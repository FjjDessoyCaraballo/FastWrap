from ..models.schemas import Completions
from ..clients.redis_client import redis_client as r
from fastapi import HTTPException, status
import logging
import json
 
logger = logging.getLogger(__name__)

async def store_message(request: Completions):
    try: 
        await r.rpush(f"chat:{request.uuid}", json.dumps({"role": request.role, "content": request.content}))
        messages = await r.lrange(f"chat:{request.uuid}", 0, -1)
        parsed = [json.loads(msg) for msg in messages]
        logging.info(f"Parsed request: {parsed}")
        await r.expire(f"chat:{request.uuid}", 300)
        return status.HTTP_201_CREATED
    except HTTPException as e: # (status_code=500, detail=str(e))
        logger.error(f"Network error caught: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error caught: {e}")
        raise 
