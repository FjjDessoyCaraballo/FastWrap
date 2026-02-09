from __future__ import annotations

"""Integration-ish test for: /api/chat <-> pgvector memory.

This runs the FastAPI app in-process (ASGITransport), but:
- does NOT call a real LLM (ChatBot is monkeypatched)
- does NOT call a real embeddings API (vector_service.embed_text is monkeypatched)
- does NOT require Redis (app.chat.service.r is monkeypatched with an in-memory fake)

It *does* require a working Postgres DATABASE_URL because your app uses asyncpg.
"""

import hashlib
import math
import re
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


def _schema_embedding_dim() -> int:
    schema_path = Path(__file__).resolve().parents[1] / "app" / "database" / "schema.sql"
    text = schema_path.read_text(encoding="utf-8")
    m = re.search(r"\bembedding\s+vector\((\d+)\)", text)
    if not m:
        m = re.search(r"\bvector\((\d+)\)", text)
    if not m:
        raise AssertionError(f"Could not find vector(N) dimension in {schema_path}")
    return int(m.group(1))


def _deterministic_vector(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals = [((digest[i % 32] / 255.0) * 2.0 - 1.0) for i in range(dim)]
    norm = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / norm for v in vals]


class FakeRedis:
    def __init__(self):
        self.data: dict[str, list[str]] = {}
        self.expires: dict[str, int] = {}

    async def rpush(self, key: str, value: str):
        self.data.setdefault(key, []).append(value)

    async def lpush(self, key: str, value: str):
        self.data.setdefault(key, []).insert(0, value)

    async def llen(self, key: str) -> int:
        return len(self.data.get(key, []))

    async def lrange(self, key: str, start: int, end: int):
        lst = self.data.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start : end + 1]

    async def expire(self, key: str, seconds: int):
        self.expires[key] = seconds


# Capture of the messages passed into the LLM call (fake)
_LLM_CAPTURE: dict[str, object] = {"last": None}


@pytest.fixture(autouse=True)
def _mock_embeddings(monkeypatch):
    dim = _schema_embedding_dim()

    async def fake_embed_text(text: str) -> list[float]:
        return _deterministic_vector(text, dim)

    import app.vectors.service as vector_service
    # service.py does: `from .embeddings import embed_text`
    monkeypatch.setattr(vector_service, "embed_text", fake_embed_text)


@pytest.fixture(autouse=True)
def _mock_llm_and_redis(monkeypatch):
    """Stop the test from calling a real model, and remove Redis dependency."""

    # Patch ChatBot so __init__ doesn't build a real LangChain agent.
    import app.agents.chatbot_agent as chatbot_agent

    def fake_init(self):
        return None

    async def fake_chat(self, parsed_messages):
        _LLM_CAPTURE["last"] = parsed_messages
        return {"messages": [{"role": "assistant", "content": "ASSISTANT REPLY"}]}
    
    async def fake_context(self, uuid: str, store_id: str):
        # Keep it simple: a stable system prompt.
        return "SYSTEM PROMPT"
    monkeypatch.setattr(chatbot_agent.ChatBot, "__init__", fake_init)
    monkeypatch.setattr(chatbot_agent.ChatBot, "chat", fake_chat)
    monkeypatch.setattr(chatbot_agent.ChatBot, "context", fake_context)
    # Patch Redis client used by chat service.
    import app.chat.service as chat_service
    fake_r = FakeRedis()
    monkeypatch.setattr(chat_service, "r", fake_r)


@pytest.mark.asyncio(loop_scope="module")
async def test_chat_wires_vector_retrieval_and_stores_chat_turns(authenticated_user):
    """End-to-end-ish:
    1) Upsert a KB snippet (entity_type != chat)
    2) Call /api/chat with a query designed to match the snippet
    3) Assert the prompt sent to the LLM included retrieved KB context
    4) Assert user's chat text was stored as entity_type='chat' (vector-searchable)
    """

    character_id = str(uuid.uuid4())  # request.uuid is used as the "character" id in chat
    kb_text = "Shipping policy: delivery in 2-5 business days."
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # (1) store KB memory
        up = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "policy", "entity_id": str(uuid.uuid4()), "content": kb_text},
        )
        assert up.status_code == 201, f"KB upsert failed: {up.status_code} {up.text}"
        # (2) call chat with a query that will deterministically retrieve kb_text
        chat_payload = {"uuid": character_id, "role": "user", "content": kb_text}
        ch = await ac.post(
            "/api/chat",
            headers={"x-api-key": authenticated_user.api_key},
            json=chat_payload,
        )
    assert ch.status_code == 201, f"Chat failed: {ch.status_code} {ch.text}"
    # (3) verify retrieval context was injected into the LLM prompt
    seen = _LLM_CAPTURE.get("last")
    assert isinstance(seen, list) and seen, "LLM was never called (fake_chat didn't run)"
    # Expect a system message containing the retrieved KB content.
    injected = [m for m in seen if isinstance(m, dict) and m.get("role") == "system" and kb_text in (m.get("content") or "")]
    assert injected, "Expected retrieved KB context to be injected as a system message"
    # (4) verify chat memory is searchable via /api/vectors/search (entity_type='chat')
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s1 = await ac.post(
            "/api/vectors/search",
            headers={"x-api-key": authenticated_user.api_key},
            json={"query": chat_payload["content"], "top_k": 10, "entity_type": "chat"},
        )
    assert s1.status_code == 200, f"Vector search failed: {s1.status_code} {s1.text}"
    rows = s1.json().get("data")
    assert isinstance(rows, list)
    assert any(r.get("content") == chat_payload["content"] for r in rows), (
        "Expected user's chat message to be stored as entity_type='chat' in embeddings"
    )