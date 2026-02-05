from ..models.schemas import Completions
from ..infrastructure.redis_client import redis_client as r
from fastapi import HTTPException
from ..agents.chatbot_agent import ChatBot
from typing import Any
from config import settings
import json
import logging

logger = logging.getLogger(__name__)

async def store_message(request: Completions, store_id: str):
    try:

        await r.rpush(f"chat:{store_id}:{request.uuid}", json.dumps({"role": request.role, "content": request.content}))
        messages: list[str] = await r.lrange(f"chat:{store_id}:{request.uuid}", 0, -1)
        parsed: list[dict[str, str]] = [json.loads(msg) for msg in messages]
        count_llen = await r.llen(f"chat:{store_id}:{request.uuid}")

        logging.debug(f"Parsed request for {request.uuid}")
        logger.info(f"count_llen: {count_llen}")

        logger.info(f"Parsed payload: {parsed}")
        logger.info(f"Messages: {messages}")
        chatbot = ChatBot()

        if count_llen == 1:
            status_code: int
            context = await chatbot.context(parsed, request.uuid, store_id)
            logger.info(f"context: {context}")
            if context is None:
                return None
            await r.lpush(f"chat:{store_id}:{request.uuid}", json.dumps({"role": "system", "content": context}))
            messages: list[str] = await r.lrange(f"chat:{store_id}:{request.uuid}", 0, -1)
            parsed: list[dict[str, str]] = [json.loads(msg) for msg in messages]

        response: dict[str, Any]
        response = await chatbot.chat(parsed)

        await r.expire(f"chat:{store_id}:{request.uuid}", 1200)
        return response

    except HTTPException as e:
        logger.error(f"Network error caught: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error at store_message caught: {e}")
        return None
