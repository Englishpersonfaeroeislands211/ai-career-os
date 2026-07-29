"""Turn text into vectors and find the most relevant resume chunks."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from app.schemas.rag import ResumeChunk, ScoredChunk


class EmbeddingProvider(Protocol):
    """Embed a batch of texts into same-dimensional vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class DeterministicEmbeddingProvider:
    """Bag-of-words vectors for unit tests — fast, offline, no model download.

    Not semantically rich; only guarantees overlapping tokens score higher.
    """

    model_name = "deterministic-test"

    def __init__(self, dims: int = 384) -> None:
        self.dims = dims

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_normalize(_bag_of_words(text, self.dims)) for text in texts]


class FastEmbedProvider:
    """Local ONNX embeddings via fastembed (used in production match retrieval)."""

    model_name = "BAAI/bge-small-en-v1.5"

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model_name = model_name
        self._model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        return [vector.tolist() for vector in model.embed(texts)]

    def _get_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_name)
        return self._model


_default_provider: FastEmbedProvider | None = None


def get_embedding_provider() -> FastEmbedProvider:
    """Return a process-local fastembed provider (lazy model load)."""
    global _default_provider
    if _default_provider is None:
        _default_provider = FastEmbedProvider()
    return _default_provider


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def retrieve_chunks(
    query: str,
    chunks: list[ResumeChunk],
    embedder: EmbeddingProvider,
    *,
    top_k: int = 15,
) -> list[ScoredChunk]:
    """Rank resume chunks by cosine similarity to the query embedding."""
    if not chunks or top_k <= 0:
        return []

    texts = [query, *[chunk.text for chunk in chunks]]
    vectors = embedder.embed(texts)
    query_vector = vectors[0]
    chunk_vectors = vectors[1:]

    scored = [
        ScoredChunk(chunk=chunk, score=cosine_similarity(query_vector, vector))
        for chunk, vector in zip(chunks, chunk_vectors, strict=True)
    ]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[: min(top_k, len(scored))]


def _bag_of_words(text: str, dims: int) -> list[float]:
    vector = [0.0] * dims
    for token in _tokenize(text):
        index = int(hashlib.md5(token.encode()).hexdigest(), 16) % dims
        vector[index] += 1.0
    return vector


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
