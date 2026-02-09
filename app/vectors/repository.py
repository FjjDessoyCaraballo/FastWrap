import logging
import uuid
from typing import Any, Optional
import asyncpg
from pgvector import Vector
from ..database.init import init_db

logger = logging.getLogger(__name__)


class VectorRepo:
    """Minimal pgvector-backed repository."""

    async def upsert_embedding(
        self,
        client_id: str,
        *,
        entity_type: str,
        entity_id: str,
        content: str,
        embedding: list[float],
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        try:
            cid = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            eid = entity_id if isinstance(entity_id, uuid.UUID) else uuid.UUID(entity_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO embeddings (client_id, entity_type, entity_id, content, embedding, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                    ON CONFLICT (client_id, entity_type, entity_id) WHERE deleted_at IS NULL
                    DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = now(),
                        deleted_at = NULL
                    RETURNING id, client_id, entity_type, entity_id, content, metadata, created_at, updated_at
                    """,
                    cid,
                    entity_type,
                    eid,
                    content,
                    Vector(embedding),
                    metadata
                )
            return dict(row) if row else None
        except (ValueError, TypeError):
            logger.exception("Invalid UUID passed to VectorRepo.upsert_embedding")
            return None
        except asyncpg.PostgresError:
            logger.exception("Database error in VectorRepo.upsert_embedding")
            return None

    async def search(
        self,
        client_id: str,
        *,
        query_embed: list[float],
        top_k: int = 5,
        entity_type: Optional[str] = None,
        metadata_filter: Optional[dict[str, Any]] = None,
        exclude_entity_type: Optional[str] = None
    ) -> list[dict[str, Any]]:
        try:
            cid = client_id if isinstance(client_id, uuid.UUID) else uuid.UUID(client_id)
            pool = await init_db()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        id, client_id, entity_type, entity_id, content, metadata,
                        (embedding <=> $1) AS distance,
                        created_at, updated_at
                    FROM embeddings
                    WHERE client_id = $2
                      AND deleted_at IS NULL
                      AND ($3::text IS NULL OR entity_type = $3)
                      AND ($4::jsonb IS NULL OR metadata @> $4::jsonb)
                      AND ($5::text IS NULL OR entity_type <> $5)
                    ORDER BY embedding <=> $1
                    LIMIT $6
                    """,
                    Vector(query_embed),
                    cid,
                    entity_type,
                    metadata_filter,
                    exclude_entity_type,
                    int(top_k)
                )
            return [dict(r) for r in rows]
        except (ValueError, TypeError):
            logger.exception("Invalid UUID passed to VectorRepo.search")
            return []
        except asyncpg.PostgresError:
            logger.exception("Database error in VectorRepo.search")
            return []
