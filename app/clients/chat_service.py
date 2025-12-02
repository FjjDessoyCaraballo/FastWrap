from ..models.schemas import Completions
from ..clients.redis_client import redis_client as r
from fastapi import HTTPException, status
from ..agents.chatbot_agent import ChatBot
from typing import Any
import logging
import json

logger = logging.getLogger(__name__)

async def store_message(request: Completions, character_uuid: str):
    try: 
        
        await r.rpush(f"chat:{character_uuid}:{request.uuid}", json.dumps({"role": request.role, "content": request.content}))
        messages: list[str] = await r.lrange(f"chat:{character_uuid}:{request.uuid}", 0, -1)
        parsed: list[dict[str, str]] = [json.loads(msg) for msg in messages]
        count_llen = await r.llen(f"chat:{character_uuid}:{request.uuid}")
        
        logging.debug(f"Parsed request for {request.uuid}")
        logger.info(f"count_llen: {count_llen}")
        
        chatbot = ChatBot()

        # Adding RAG for first time conversations
        if count_llen == 1:
            status_code: int
            rag, status_code = await chatbot.rag(parsed, character_uuid)
            await r.lpush(f"chat:{character_uuid}:{request.uuid}", json.dumps({"role": "system", "content": rag}))
            messages: list[str] = await r.lrange(f"chat:{character_uuid}:{request.uuid}", 0, -1)
            parsed: list[dict[str, str]] = [json.loads(msg) for msg in messages]

        response: dict[str, Any]
        response = await chatbot.chat(parsed)
    
        await r.expire(f"chat:{character_uuid}:{request.uuid}", 300)
        return status.HTTP_201_CREATED, response

    except HTTPException as e:
        logger.error(f"Network error caught: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error caught: {e}")
        raise 
