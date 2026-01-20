import logging
from typing import Optional, List
from config import settings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

_embeddings: Optional[OpenAIEmbeddings] = None

def get_embeddings_client() -> OpenAIEmbeddings:
    """Return a configured LangChain embeddings client."""
    global _embeddings
    if _embeddings is None:
        model = settings.EMBEDDING_MODEL
        dimensions = settings.EMBEDDING_DIM
        api_key = settings.MODEL_KEY
        kwargs = {'model': model, 'api_key': api_key}
        if dimensions is not None:
            kwargs['dimensions'] = int(dimensions)
        _embeddings = OpenAIEmbeddings(**kwargs)
        logger.info('Embeddings client initialized (model=%s), dimensions=%s', model, dimensions)
    return _embeddings

async def embed_text(text: str) -> List[float]:
    """Compute an embedding for a single text."""
    embedder = get_embeddings_client()
    return await embedder.aembed_query(text)
