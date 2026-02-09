from __future__ import annotations
import logging
import uuid
from typing import Any, Optional
from config import settings
from ..vectors import service as vector_service

logger = logging.getLogger(__name__)

def _truncate(text: str, max_char: int) -> str:
    if max_char <= 0:
        return text
    if len(text) <= max_char:
        return text
    return text[: max_char + 1] + "..."

async def store_chat_turn(*,
    store_id: str,
    character_id: str,
    role: str,
    content: str,
    extra_metadata: Optional[dict[str, Any]] = None    
) -> None:
	"""Persist one chat turn into pgvector as long-term memory."""
	
	if not getattr(settings, "VECTOR_CHAT_STORE_ENABLED", True):
		return
	if not content:
		return
	entity_type = getattr(settings, "VECTOR_CHAT_ENTITY_TYPE", "chat")
	entity_id = str(uuid.uuid4())
	metadata: dict[str, Any] = {
		"character_id": character_id,
		"role": role
	}
	if extra_metadata:
		metadata.update(extra_metadata)
	try:
		await vector_service.upsert_text_snippet(
			client_id=str(store_id),
			entity_type=entity_type,
			entity_id=entity_id,
			content=content,
			metadata=metadata
		)
	except Exception:
		logger.exception("Failed to store chat turn in the db")

async def build_vector_context(
	*,
	store_id: str,
	character_id: str,
	query: str
) -> Optional[str]:
	"""Retrieve relevant long-term memory snippets and format them for the LLM."""

	if not getattr(settings, "VECTOR_CHAT_MEMORY_ENABLED", True):
		return None
	if not query:
		return None
	top_k_chat = int(getattr(settings, "VECTOR_CHAT_MEMORY_TOP_K_CHAT", 4))
	top_k_kb = int(getattr(settings, "VECTOR_CHAT_MEMORY_TOP_K_KB", 4))
	max_chars = int(getattr(settings, "VECTOR_CHAT_MEMORY_MAX_CHARS", 2400))
	chat_type = getattr(settings, "VECTOR_CHAT_ENTITY_TYPE", "chat")
	try:
		# 1) Chat-scoped memory (only this character/conversation)
		chat_rows = await vector_service.semantic_search(
			client_id=str(store_id),
			query=query,
			top_k=top_k_chat,
			entity_type=chat_type,
			metadata_filter={"character_id": character_id}
		)
		# 2) Store-level KB (everything except chat turns)
		kb_rows = await vector_service.semantic_search(
			client_id=str(store_id),
			query=query,
			top_k=top_k_kb,
			entity_type=None,
			exclude_entity_type=chat_type
		)
		rows = chat_rows + kb_rows
		if not rows:
			return None
		lines: list[str] = [
			"Relevant context from long-term memory. Use only if it helps answer the user."
		]
		# Deduplicate by content (cheap and good enough for now)
		seen: set[str] = set()
		for r in rows:
			content = (r.get("content") or "").strip()
			if not content or content in seen:
				continue
			seen.add(content)
			tag = r.get("entity_type") or "memory"
			lines.append(f"- [{tag}] {_truncate(content, 500)}")
			if sum(len(x) + 1 for x in lines) > max_chars:
				break
		if len(lines) == 1:
			return None
		return _truncate("\n".join(lines), max_chars)
	except Exception:
		logger.exception("Failed to build vector retrieval context")
		return None