import logging
from typing import Any, Optional
from .embeddings import embed_text
from .repository import VectorRepo

logger = logging.getLogger(__name__)

async def upsert_text_snippet(*, client_id: str, entity_type: str, entity_id: str, content: str,
                                metadata: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    try:
        embed = await embed_text(content)
        repo = VectorRepo()
        return await repo.upsert_embedding(client_id, entity_type=entity_type, entity_id=entity_id,
                                            content=content, embedding=embed, metadata=metadata)
    except Exception as e:
        logger.error(f"Failed to upsert snippet: {e}")
        return None

async def semantic_search(*, client_id: str, query: str, top_k: int = 5,
                            entity_type: Optional[str] = None) -> list[dict[str, Any]]:
    try:
        query_embed = await embed_text(query)
        repo = VectorRepo()
        return await repo.search(client_id, query_embed=query_embed, top_k=top_k,
                                    entity_type=entity_type)
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []