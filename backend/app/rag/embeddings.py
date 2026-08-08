"""
Embedding generation.

Uses a local sentence-transformers model (all-MiniLM-L6-v2, 384-dim) so
Phase 1 has zero dependency on a paid embeddings API. The model is
loaded lazily and cached as a module-level singleton.
"""
import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning plain python lists (pgvector-friendly)."""
    if not texts:
        return []
    model = _get_model()
    vectors: np.ndarray = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
