from __future__ import annotations
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

        chatbot = ChatBot()
        if count_llen == 1:
            system_prompt = await chatbot.context(request.uuid, store_id)
            logger.info(f"system_prompt fetched for {request.uuid}: {bool(system_prompt)}")
            if system_prompt is None:
                return None
            # Prepend system prompt to the conversation
            await r.lpush(chat_key, json.dumps({"role": "system", "content": system_prompt}))
        # 3) Load conversation from Redis               
        messages: list[str] = await r.lrange(chat_key, 0, -1)
        parsed: list[dict[str, str]] = [json.loads(msg) for msg in messages]
        # logging.debug(f"Parsed request for {request.uuid}")
        logger.info(f"count_llen: {count_llen}")
        logger.info(f"Parsed payload: {parsed}")
        # logger.info(f"Messages: {messages}")
        # 4) Retrieve vector memory (ephemeral injection, not stored in Redis)
        parsed_for_llm = parsed[:]
        if request.role == "user":
            retrieved = await build_vector_context(
                store_id=store_id,
                character_id=request.uuid,
                query=request.content
            )
            if retrieved:
                insert_at = 1 if parsed_for_llm and parsed_for_llm[0].get("role") == "system" else 0
                parsed_for_llm.insert(insert_at, {"role": "system", "content": retrieved})
        # 5) Call the model
        response: dict[str, Any] = await chatbot.chat(parsed_for_llm)
        # 6) Extract assistant reply and store it in Redis
        assistant_text = _extract_assistant_text(response)
        if assistant_text:
            await r.rpush(chat_key, json.dumps({"role": "assistant", "content": assistant_text}))
        # 7) Store long-term memory in pgvector
        # Store the incoming user turn (if applicable) and the assistant reply.
        if request.role == "user":
            await store_chat_turn(
                store_id=store_id,
                character_id=request.uuid,
                role="user",
                content=request.content
            )
        if assistant_text:
            await store_chat_turn(
                store_id=store_id,
                character_id=request.uuid,
                role="assistant",
                content=assistant_text
            )
        # 8) TTL for Redis chat buffer
        await r.expire(chat_key, 1200)
        return response   
    except HTTPException as e:
        logger.error(f"Network error caught: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error at store_message caught: {e}")
        return None
