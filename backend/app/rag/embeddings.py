"""
Embedding generation.

Uses `fastembed` (ONNX Runtime, not PyTorch) running the SAME model as
before — `sentence-transformers/all-MiniLM-L6-v2`, 384-dim — so the
pgvector schema, similarity math, and everything downstream (retriever,
seed script) are completely unchanged. Only the runtime changed.

Why: the original implementation used the `sentence-transformers`
package, which pulls in PyTorch. Torch's CPU wheel alone typically adds
several hundred MB of RSS on import, which — combined with the rest of
this app's dependency graph (LangGraph, LangChain, SQLAlchemy, reportlab,
python-docx, etc.) — reliably exceeded the 512MB ceiling on Render's
free tier and got the process OOM-killed during startup, before it
could even bind its port. `fastembed` uses `onnxruntime` instead, which
has a dramatically smaller memory footprint and needs no GPU/CUDA
stubs, while producing embeddings for the same model.

The model is loaded lazily (only on the first actual embedding call,
not at process boot) and cached as a module-level singleton, same as
before.
"""
import logging
from functools import lru_cache

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_model():
    from fastembed import TextEmbedding  # deferred — see module docstring
    logger.info("Loading embedding model (fastembed/onnxruntime): %s", settings.embedding_model)
    return TextEmbedding(model_name=settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning plain python lists (pgvector-friendly)."""
    if not texts:
        return []
    model = _get_model()
    vectors = list(model.embed(texts))  # fastembed returns a generator of np.ndarray
    normalized = [_l2_normalize(v) for v in vectors]
    return [v.tolist() for v in normalized]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def _l2_normalize(vector: np.ndarray) -> np.ndarray:
    """L2-normalize so vector magnitude is consistent with the previous
    sentence-transformers(normalize_embeddings=True) behavior. Not
    strictly required for pgvector's cosine_distance operator (which is
    scale-invariant), but keeps stored vectors consistent/comparable."""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm