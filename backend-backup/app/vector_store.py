
"""In-memory TurboVec vector store for DevAssist."""

from __future__ import annotations

from typing import Any

import numpy as np
from turbovec import IdMapIndex


class VectorStore:
    """Store document chunks and search their normalized embeddings."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim
        self._index = IdMapIndex(dim=dim, bit_width=4)
        self._next_id = 0
        self._chunks: dict[int, dict[str, Any]] = {}
        self._sources: set[str] = set()
        self._vectors: dict[int, np.ndarray] = {}

    @property
    def backend(self) -> str:
        return "turbovec"

    @property
    def chunks(self) -> list[dict[str, Any]]:
        return list(self._chunks.values())

    @property
    def sources(self) -> set[str]:
        return set(self._sources)

    def __len__(self) -> int:
        return len(self._chunks)

    def add(
        self,
        embeddings: np.ndarray,
        chunks: list[Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Add document chunks and their corresponding embeddings."""
        vectors = np.asarray(embeddings, dtype=np.float32)

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError(
                f"Expected embeddings with dimension {self.dim}"
            )

        if len(chunks) != len(vectors):
            raise ValueError(
                "Number of chunks must match number of embeddings"
            )

        if len(vectors) == 0:
            return

        if not np.isfinite(vectors).all():
            raise ValueError("Embeddings must contain only finite values")

        # Normalize vectors so dot products correspond to cosine similarity.
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.maximum(norms, 1e-12)

        ids = np.arange(
            self._next_id,
            self._next_id + len(vectors),
            dtype=np.uint64,
        )

        # TurboVec requires a 1-D uint64 ID array.
        # Insert before updating metadata to avoid inconsistent state
        # if the index rejects the insertion.
        self._index.add_with_ids(vectors, ids)

        for vector_id, vector, chunk in zip(ids, vectors, chunks):
            key = int(vector_id)

            if isinstance(chunk, dict):
                record = dict(chunk)
            else:
                record = {"text": str(chunk)}

            record.setdefault("filename", "unknown")
            record.setdefault("chunk_index", key)

            self._chunks[key] = record
            self._vectors[key] = vector.copy()
            self._sources.add(str(record["filename"]))

        self._next_id += len(vectors)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 3,
        filename_filter: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Return the highest-scoring chunks for a query."""
        if k <= 0 or not self._chunks:
            return []

        query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)

        if query.shape[0] != self.dim:
            raise ValueError(
                f"Expected query dimension {self.dim}"
            )

        if not np.isfinite(query).all():
            raise ValueError("Query embedding must contain finite values")

        norm = float(np.linalg.norm(query))
        if norm == 0:
            return []

        query = query / norm

        candidates = [
            vector_id
            for vector_id, record in self._chunks.items()
            if filename_filter is None
            or record.get("filename") == filename_filter
        ]

        if not candidates:
            return []

        # Use the retained normalized vectors to preserve cosine ranking
        # and ensure filename filtering matches the returned metadata.
        scores = {
            vector_id: float(np.dot(self._vectors[vector_id], query))
            for vector_id in candidates
        }

        ranked_ids = sorted(
            candidates,
            key=lambda vector_id: scores[vector_id],
            reverse=True,
        )

        return [
            {
                **self._chunks[vector_id],
                "score": scores[vector_id],
            }
            for vector_id in ranked_ids[:k]
        ]

    def search_with_metadata(
        self,
        query_embedding: np.ndarray,
        k: int = 3,
        filename_filter: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search and return chunks with metadata and similarity scores."""
        return self.search(
            query_embedding,
            k=k,
            filename_filter=filename_filter,
            **kwargs,
        )

    def get_file_list(self) -> list[str]:
        """Return the distinct source filenames."""
        return sorted(self._sources)

    def clear(self) -> None:
        """Clear the index, vectors, IDs, and associated metadata."""
        self._index = IdMapIndex(dim=self.dim, bit_width=4)
        self._next_id = 0
        self._chunks.clear()
        self._sources.clear()
        self._vectors.clear()
