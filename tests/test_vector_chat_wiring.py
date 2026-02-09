"""Tests for the pgvector <-> chat wiring.
Goal: verify the chat pipeline:
- injects system prompt exactly once
- performs vector retrieval (ephemeral prompt injection)
- stores assistant replies in Redis
- stores chat turns in pgvector via the vector service
These tests are mostly unit-ish and rely on monkeypatching to avoid:
- real Redis
- real Postgres
- real OpenAI embeddings
- real LLM calls
Run from project root:
  pytest -q
"""

from __future__ import annotations
import pathlib
import py_compile
import uuid
import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]

def _path(*parts: str) -> pathlib.Path:
    return PROJECT_ROOT.joinpath(*parts)

CRITICAL_SOURCES = [
    _path("app", "chat", "service.py"),
    _path("app", "chat", "memory.py"),
    _path("app", "vectors", "repository.py"),
    _path("app", "vectors", "service.py"),
    _path("app", "agents", "chatbot_agent.py"),
]

def _compiles(path: pathlib.Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except Exception:
        return False

def test_critical_sources_compile() -> None:
    """Fail fast on syntax errors.
    If this fails, nothing else matters because your API won't even start.
    """
    for p in CRITICAL_SOURCES:
        py_compile.compile(str(p), doraise=True)


# ------------------------- memory.py tests -------------------------

@pytest.mark.asyncio
async def test_build_vector_context_calls_semantic_search_with_metadata_filter(monkeypatch):
    from app.chat import memory

    calls: list[dict] = []

    async def fake_semantic_search(*, client_id, query, top_k=5, entity_type=None, metadata_filter=None, exclude_entity_type=None):
        calls.append(
            {
                "client_id": client_id,
                "query": query,
                "top_k": top_k,
                "entity_type": entity_type,
                "metadata_filter": metadata_filter,
                "exclude_entity_type": exclude_entity_type,
            }
        )
        # Return one fake row for the chat-scoped query, none for KB.
        if entity_type == "chat":
            return [{"content": "Previously: shipping is 2-5 days", "entity_type": "chat"}]
        return []
    monkeypatch.setattr(memory.vector_service, "semantic_search", fake_semantic_search)
    store_id = str(uuid.uuid4())
    character_id = str(uuid.uuid4())
    # Should not raise, should call semantic_search twice.
    result = await memory.build_vector_context(store_id=store_id, character_id=character_id, query="shipping time")
    assert calls, "semantic_search was never called"
    assert len(calls) == 2, f"Expected 2 semantic_search calls (chat+kb), got {len(calls)}"
    # First call should scope chat memory by character.
    assert calls[0]["entity_type"] == "chat"
    assert calls[0]["metadata_filter"] == {"character_id": character_id}
    assert isinstance(result, str)
    assert "shipping" in result.lower()


@pytest.mark.asyncio
async def test_store_chat_turn_writes_character_uuid_metadata(monkeypatch):
    from app.chat import memory
    captured = {}
    async def fake_upsert_text_snippet(*, client_id, entity_type, entity_id, content, metadata=None):
        captured.update(
            {
                "client_id": client_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "content": content,
                "metadata": metadata,
            }
        )
        return {"ok": True}
    monkeypatch.setattr(memory.vector_service, "upsert_text_snippet", fake_upsert_text_snippet)
    await memory.store_chat_turn(
        store_id=str(uuid.uuid4()),
        character_id=str(uuid.uuid4()),
        role="user",
        content="hello",
    )
    assert "metadata" in captured
    assert "character_id" in captured["metadata"], "metadata should include character_id for scoped retrieval"


# ------------------------- repository.py tests -------------------------

@pytest.mark.asyncio
async def test_vector_repo_search_uses_metadata_filter_and_exclude_entity_type(monkeypatch):
    from app.vectors.repository import VectorRepo

    class FakeConn:
        def __init__(self):
            self.query = None
            self.args = None

        async def fetch(self, query, *args):
            self.query = query
            self.args = args
            return []

    class _Acquire:
        def __init__(self, conn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakePool:
        def __init__(self, conn):
            self._conn = conn

        def acquire(self):
            return _Acquire(self._conn)

    fake_conn = FakeConn()

    async def fake_init_db():
        return FakePool(fake_conn)

    # Patch init_db inside the repository module.
    import app.vectors.repository as repo_mod

    monkeypatch.setattr(repo_mod, "init_db", fake_init_db)

    repo = VectorRepo()

    client_id = str(uuid.uuid4())
    query_embed = [0.0] * 1536

    await repo.search(
        client_id,
        query_embed=query_embed,
        top_k=3,
        entity_type="chat",
        metadata_filter={"character_id": "abc"},
        exclude_entity_type="chat",
    )

    assert fake_conn.query is not None, "repo.search did not execute a query"

    q = fake_conn.query
    # We expect both filters to exist.
    assert "metadata @>" in q, "search query must support metadata_filter via JSONB containment"
    assert "entity_type <>" in q, "search query must support exclude_entity_type"

    # Args order should be: vector, client_id, entity_type, metadata_filter, exclude_entity_type, top_k
    assert fake_conn.args is not None
    assert fake_conn.args[2] == "chat"
    assert fake_conn.args[3] == {"character_id": "abc"}
    assert fake_conn.args[4] == "chat"


# ------------------------- chat/service.py wiring tests -------------------------

SERVICE_COMPILES = _compiles(_path("app", "chat", "service.py"))


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


@pytest.mark.asyncio
@pytest.mark.skipif(not SERVICE_COMPILES, reason="app/chat/service.py has syntax errors")
async def test_store_message_injects_retrieval_stores_assistant_and_upserts_turns(monkeypatch):
    # Import after compile guard
    from app.chat import service as chat_service

    fake_r = FakeRedis()
    monkeypatch.setattr(chat_service, "r", fake_r)

    # Fake ChatBot that records what messages were sent.
    class FakeChatBot:
        def __init__(self):
            self.seen = None

        async def context(self, uuid: str, store_id: str):
            return "SYSTEM PROMPT"

        async def chat(self, parsed_messages):
            self.seen = parsed_messages
            # Mimic agent response shape
            return {"messages": [{"role": "assistant", "content": "ASSISTANT REPLY"}]}

    monkeypatch.setattr(chat_service, "ChatBot", FakeChatBot)

    # Retrieval context should be inserted ephemerally.
    async def fake_build_vector_context(*, store_id, character_id, query):
        return "RETRIEVED MEMORY"

    monkeypatch.setattr(chat_service, "build_vector_context", fake_build_vector_context)
    upsert_calls = []

    async def fake_store_chat_turn(*, store_id, character_id, role, content, extra_metadata=None):
        upsert_calls.append({"store_id": store_id, "character_id": character_id, "role": role, "content": content})

    monkeypatch.setattr(chat_service, "store_chat_turn", fake_store_chat_turn)

    from app.models.schemas import Completions

    store_id = str(uuid.uuid4())
    character_id = str(uuid.uuid4())
    req = Completions(uuid=character_id, role="user", content="Hello")
    response = await chat_service.store_message(req, store_id)
    assert response
    chat_key = f"chat:{store_id}:{character_id}"
    # Redis should contain: system prompt + user + assistant
    assert await fake_r.llen(chat_key) == 3
    # Assistant reply should have been stored
    stored = await fake_r.lrange(chat_key, 0, -1)
    assert any("ASSISTANT REPLY" in s for s in stored)
    # Retrieval should NOT be persisted in Redis
    assert not any("RETRIEVED MEMORY" in s for s in stored)
    # Upserts should include user turn and assistant turn
    roles = [c["role"] for c in upsert_calls]
    assert roles == ["user", "assistant"]
    # User content should be the user's message, not assistant_text
    assert upsert_calls[0]["content"] == "Hello"
    assert upsert_calls[1]["content"] == "ASSISTANT REPLY"