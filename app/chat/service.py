from __future__ import annotations
import json
import logging
from typing import Any, Optional
from fastapi import HTTPException
from config import settings
from ..agents.chatbot_agent import ChatBot
from ..infrastructure.redis_client import redis_client as r
from ..models.schemas import Completions
from .memory import build_vector_context, store_chat_turn

logger = logging.getLogger(__name__)


def _extract_assistant_text(response: Any) -> Optional[str]:
    """
    Best-effort extraction of assistant text from LangChain agent responses.

    Common shapes:
      - {"messages": [SystemMessage, HumanMessage, AIMessage, ...]}
      - {"messages": [{"role": "...", "content": "..."}, ...]}
      - {"output": "..."} or {"text": "..."} or {"final": "..."}
      - AIMessage-like object with .content
      - plain string
    """
    if response is None:
        return None
    if isinstance(response, str):
        text = response.strip()
        return text or None
    content = getattr(response, "content", None)
    if isinstance(content, str):
        text = content.strip()
        return text or None
    if isinstance(response, dict):
        messages = response.get("messages")
        if isinstance(messages, list):
            for msg in reversed(messages):
                # dict-style messages
                if isinstance(msg, dict):
                    if msg.get("role") in {"assistant", "ai"} and isinstance(msg.get("content"), str):
                        text = msg["content"].strip()
                        return text or None
                    continue
                # object-style messages (LangChain BaseMessage)
                msg_type = getattr(msg, "type", None)  # "ai", "human", "system"
                msg_content = getattr(msg, "content", None)
                if msg_type in {"ai", "assistant"} and isinstance(msg_content, str):
                    text = msg_content.strip()
                    return text or None
                if msg.__class__.__name__ == "AIMessage" and isinstance(msg_content, str):
                    text = msg_content.strip()
                    return text or None
        for key in ("output", "text", "final"):
            val = response.get(key)
            if isinstance(val, str):
                text = val.strip()
                return text or None
        result = response.get("result")
        if isinstance(result, list):
            for msg in reversed(result):
                msg_content = getattr(msg, "content", None)
                if isinstance(msg_content, str):
                    text = msg_content.strip()
                    return text or None
    return None


async def store_message(request: Completions, store_id: str):
    try:
        chat_key = f"chat:{store_id}:{request.uuid}"
        await r.rpush(chat_key, json.dumps({"role": request.role, "content": request.content}))
        messages: list[str] = await r.lrange(chat_key, 0, -1)
        parsed: list[dict[str, str]] = [json.loads(msg) for msg in messages]
        count_llen = await r.llen(chat_key)

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
