import hashlib
import math
import re
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from config import settings
from main import app
from .MockUser import MockUser


def _schema_embedding_dim() -> int:
    """Parse the declared pgvector dimension from app/database/schema.sql."""
    schema_path = Path(__file__).resolve().parents[1] / "app" / "database" / "schema.sql"
    text = schema_path.read_text(encoding="utf-8")
    # Try the most specific pattern first: the embeddings column definition.
    m = re.search(r"\bembedding\s+vector\((\d+)\)", text)
    if not m:
        # Fallback: first vector(N) we see.
        m = re.search(r"\bvector\((\d+)\)", text)
    if not m:
        raise AssertionError(f"Could not find vector(N) dimension in {schema_path}")
    return int(m.group(1))


def _deterministic_vector(text: str, dim: int) -> list[float]:
    """Deterministic, dependency-free fake embedding with a stable output."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()  # 32 bytes
    vals = [((digest[i % 32] / 255.0) * 2.0 - 1.0) for i in range(dim)]  # [-1, 1]
    # Normalize so cosine distance behaves predictably.
    norm = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / norm for v in vals]


async def _store_id_from_api_key(api_key: str) -> str:
    """
    Your vector service functions require client_id (store_id).
    Endpoints hide it behind verify_api_key, so for service-level tests we fetch it via DB.
    """
    from app.clients.repository import crud_management

    crud = crud_management()
    row = await crud.db_select_client_by_key(api_key)
    assert row is not None, "Could not resolve store_id from api_key"
    return str(row[0])


@pytest.fixture(autouse=True)
def _mock_embeddings(monkeypatch):
    """Avoid calling external embedding APIs during tests."""
    dim = _schema_embedding_dim()

    async def fake_embed_text(text: str) -> list[float]:
        return _deterministic_vector(text, dim)

    # service.py does `from .embeddings import embed_text`, so patch the reference in service.
    import app.vectors.service as vector_service
    monkeypatch.setattr(vector_service, "embed_text", fake_embed_text)


@pytest.mark.asyncio(loop_scope="session")
async def test_vector_schema_dimension_matches_settings():
    """If this fails, your app will eventually crash when inserting vectors."""
    assert settings.EMBEDDING_DIM == _schema_embedding_dim(), (
        "EMBEDDING_DIM (config/.env) must match the DB column dimension in app/database/schema.sql"
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_vector_upsert_success(authenticated_user: MockUser):
    entity_id = str(uuid.uuid4())
    payload = {
        "entity_type": "memory",
        "entity_id": entity_id,
        "content": "Shipping policy: delivery in 2-5 business days.",
        "metadata": {"source": "pytest", "kind": "policy"},
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json=payload,
        )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json().get("data")
    assert data is not None, f"Missing data field: {response.json()}"
    assert data["entity_type"] == payload["entity_type"]
    assert str(data["entity_id"]) == entity_id
    assert data["content"] == payload["content"]


@pytest.mark.asyncio(loop_scope="session")
async def test_vector_search_returns_best_match(authenticated_user: MockUser):
    # Two different snippets
    entity_a = str(uuid.uuid4())
    entity_b = str(uuid.uuid4())
    content_a = "Return policy: 30 days with receipt."
    content_b = "Shipping policy: delivery in 2-5 business days."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "policy", "entity_id": entity_a, "content": content_a, "metadata": None},
        )
        r2 = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "policy", "entity_id": entity_b, "content": content_b, "metadata": None},
        )

    assert r1.status_code == 201, f"Upsert A failed: {r1.status_code} {r1.text}"
    assert r2.status_code == 201, f"Upsert B failed: {r2.status_code} {r2.text}"

    # Search using an exact-content query so our fake embeddings guarantee a perfect match.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s = await ac.post(
            "/api/vectors/search",
            headers={"x-api-key": authenticated_user.api_key},
            json={"query": content_b, "top_k": 1, "entity_type": "policy"},
        )

    assert s.status_code == 200, f"Expected 200, got {s.status_code}: {s.text}"
    rows = s.json().get("data")
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0]["content"] == content_b


@pytest.mark.asyncio(loop_scope="session")
async def test_vector_search_filters_by_entity_type(authenticated_user: MockUser):
    entity_policy = str(uuid.uuid4())
    entity_faq = str(uuid.uuid4())
    content_policy = "Warranty policy: 1 year manufacturer warranty."
    content_faq = "FAQ: How do I track my order?"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        rp = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "policy", "entity_id": entity_policy, "content": content_policy},
        )
        rf = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "faq", "entity_id": entity_faq, "content": content_faq},
        )
    assert rp.status_code == 201, f"Upsert policy failed: {rp.status_code} {rp.text}"
    assert rf.status_code == 201, f"Upsert faq failed: {rf.status_code} {rf.text}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s = await ac.post(
            "/api/vectors/search",
            headers={"x-api-key": authenticated_user.api_key},
            json={"query": content_policy, "top_k": 10, "entity_type": "policy"},
        )
    assert s.status_code == 200, f"Search failed: {s.status_code} {s.text}"
    rows = s.json().get("data")
    assert isinstance(rows, list)
    assert all(r["entity_type"] == "policy" for r in rows)
    assert any(r["content"] == content_policy for r in rows)


@pytest.mark.asyncio(loop_scope="session")
async def test_vector_upsert_is_idempotent_per_entity(authenticated_user: MockUser):
    """Requires a unique constraint on (client_id, entity_type, entity_id) for ON CONFLICT to work."""
    entity_id = str(uuid.uuid4())
    first = "Promo terms: 10% off for new customers."
    second = "Promo terms: 15% off for new customers (updated)."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "promo", "entity_id": entity_id, "content": first},
        )
        r2 = await ac.post(
            "/api/vectors/upsert",
            headers={"x-api-key": authenticated_user.api_key},
            json={"entity_type": "promo", "entity_id": entity_id, "content": second},
        )
    assert r1.status_code == 201, f"First upsert failed: {r1.status_code} {r1.text}"
    assert r2.status_code == 201, f"Second upsert failed: {r2.status_code} {r2.text}"
    d1 = r1.json().get("data")
    d2 = r2.json().get("data")
    assert d1 is not None and d2 is not None
    assert str(d1["entity_id"]) == entity_id
    assert str(d2["entity_id"]) == entity_id
    # Should update the same logical row (same id) if ON CONFLICT is correctly configured.
    assert str(d1["id"]) == str(d2["id"])
    assert d2["content"] == second


# ----------------------------------------------------------------------
# NEW: service-level tests for the "new" vector functions
# (metadata_filter + exclude_entity_type)
# ----------------------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_semantic_search_metadata_filter_scopes_results(authenticated_user: MockUser):
    """
    Validates: semantic_search(... metadata_filter=...) only returns rows whose metadata contains that filter.
    This is required for chat memory scoping (character_id).
    """
    import app.vectors.service as vector_service

    store_id = await _store_id_from_api_key(authenticated_user.api_key)

    char_a = str(uuid.uuid4())
    char_b = str(uuid.uuid4())

    content_a = "Chat memory: user likes apples."
    content_b = "Chat memory: user likes oranges."

    await vector_service.upsert_text_snippet(
        client_id=store_id,
        entity_type="chat",
        entity_id=str(uuid.uuid4()),
        content=content_a,
        metadata={"character_id": char_a, "role": "user"},
    )
    await vector_service.upsert_text_snippet(
        client_id=store_id,
        entity_type="chat",
        entity_id=str(uuid.uuid4()),
        content=content_b,
        metadata={"character_id": char_b, "role": "user"},
    )

    rows = await vector_service.semantic_search(
        client_id=store_id,
        query=content_a,  # exact query => deterministic perfect match with our fake embedding
        top_k=10,
        entity_type="chat",
        metadata_filter={"character_id": char_a},
    )

    assert isinstance(rows, list)
    assert rows, "Expected at least one result"
    assert all((r.get("metadata") or {}).get("character_id") == char_a for r in rows), (
        "metadata_filter must scope results by metadata @> filter"
    )
    assert any(r.get("content") == content_a for r in rows)
    assert all(r.get("content") != content_b for r in rows), "Should not leak other character's chat memory"


@pytest.mark.asyncio(loop_scope="session")
async def test_semantic_search_exclude_entity_type_works_without_metadata_filter(authenticated_user: MockUser):
    """
    Validates: semantic_search(... exclude_entity_type='chat') excludes chat rows even if metadata_filter is None.
    This is required for KB retrieval (exclude chat turns).
    """
    import app.vectors.service as vector_service

    store_id = await _store_id_from_api_key(authenticated_user.api_key)

    # Same content => identical embedding => without exclusion, chat would "win".
    shared = "Shipping policy: delivery in 2-5 business days."

    await vector_service.upsert_text_snippet(
        client_id=store_id,
        entity_type="chat",
        entity_id=str(uuid.uuid4()),
        content=shared,
        metadata={"character_id": str(uuid.uuid4()), "role": "user"},
    )
    await vector_service.upsert_text_snippet(
        client_id=store_id,
        entity_type="policy",
        entity_id=str(uuid.uuid4()),
        content=shared,
        metadata={"source": "pytest"},
    )

    rows = await vector_service.semantic_search(
        client_id=store_id,
        query=shared,
        top_k=10,
        entity_type=None,
        metadata_filter=None,
        exclude_entity_type="chat",
    )

    assert isinstance(rows, list)
    assert rows, "Expected at least one result"
    assert all(r.get("entity_type") != "chat" for r in rows), "exclude_entity_type must filter out chat rows"
    assert any(r.get("entity_type") == "policy" and r.get("content") == shared for r in rows)