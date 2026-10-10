"""In-memory TurboVec vector store (SRS 3.3) — replaced FAISS with TurboVec IdMapIndex.

Keeps the exact public interface the rest of the app relies on
(add / search / clear / __len__ / chunks / sources / backend) so main.py,
the upload endpoint and the WebSocket chat handler are untouched.

Design notes vs the upgrade-guide example:
- The guide's rebuild strategy only re-indexed *newly pending* embeddings and
  replaced the index, silently dropping previously uploaded documents.
  This store retains every embedding and adds incrementally via
  ``IdMapIndex.add_with_ids`` (verified: earlier vectors stay searchable),
  so repeated uploads can never lose documents.
- Chunk IDs are monotonic (0..n-1) and double as row positions in the
  retained embedding matrix, keeping IDs/metadata consistent across adds,
  filters and rebuilds.
- Embeddings and queries are L2-normalized on the way in (same as the old
  FAISS IndexFlatIP path), so ranking is cosine similarity.
- Falls back to a NumPy cosine index with the identical interface when
  turbovec is not installed, so the app never crashes.
"""
import numpy as np

try:
    from turbovec import IdMapIndex
    _HAS_TURBOVEC = True
except Exception:
    IdMapIndex = None
    _HAS_TURBOVEC = False

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 outputs 384-dim vectors
BIT_WIDTH = 4        # 4-bit quantization (upgrade guide recommendation)


class VectorStore:
    def __init__(self, dim: int = EMBEDDING_DIM, bit_width: int = BIT_WIDTH):
        self.dim = dim
        self.bit_width = bit_width
        self.chunks: list[str] = []
        self.sources: list[str] = []
        self._metadata: dict[int, dict] = {}  # chunk_id -> {text, filename, chunk_index}
        self._matrix: np.ndarray | None = None  # retained normalized embeddings, rows == chunk ids
        self._index = IdMapIndex(dim=dim, bit_width=bit_width) if _HAS_TURBOVEC else None

    @property
    def backend(self) -> str:
        return "turbovec" if _HAS_TURBOVEC else "numpy-fallback"

    def __len__(self) -> int:
        return len(self.chunks)

    # -- internal helpers -------------------------------------------------
    @staticmethod
    def _as_matrix(embeddings: np.ndarray) -> np.ndarray:
        emb = np.array(embeddings, dtype="float32")
        if emb.ndim == 1:
            emb = emb.reshape(1, -1)
        return emb

    def _check_dim(self, emb: np.ndarray, what: str) -> None:
        if emb.ndim != 2 or emb.shape[1] != self.dim:
            raise ValueError(f"{what} must have shape (n, {self.dim}), got {emb.shape}")

    @staticmethod
    def _normalize(emb: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return (emb / norms).astype("float32")

    # -- public API --------------------------------------------------------
    def add(self, embeddings: np.ndarray, chunks: list[str], source: str = "") -> int:
        """Add a document's chunks. Returns number of chunks added."""
        if embeddings is None or len(chunks) == 0:
            return 0
        emb = self._normalize(self._as_matrix(embeddings))
        self._check_dim(emb, "embeddings")
        start_id = len(self._metadata)  # monotonic: never reuses an id
        for i, chunk_text in enumerate(chunks):
            chunk_id = start_id + i
            self._metadata[chunk_id] = {
                "text": chunk_text,
                "filename": source,
                "chunk_index": i,
            }
        self.chunks.extend(chunks)
        self.sources.extend([source] * len(chunks))
        self._matrix = emb if self._matrix is None else np.vstack([self._matrix, emb])
        if _HAS_TURBOVEC:
            ids = np.arange(start_id, start_id + len(chunks), dtype=np.uint64)
            self._index.add_with_ids(emb, ids)
        return len(chunks)

    def search_with_metadata(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
        filename_filter: str | None = None,
    ) -> list[dict]:
        """Top-k retrieval with scores + metadata. Optional filename filter."""
        if len(self.chunks) == 0:
            return []
        q = self._normalize(self._as_matrix(query_embedding))
        self._check_dim(q, "query_embedding")

        allowed: list[int] | None = None
        if filename_filter is not None:
            allowed = [cid for cid, m in self._metadata.items()
                       if m["filename"] == filename_filter]
            if not allowed:
                return []

        pairs: list[tuple[float, int]] = []  # (score, chunk_id), best first
        if _HAS_TURBOVEC:
            allowlist = np.array(allowed, dtype=np.uint64) if allowed is not None else None
            scores, ids = self._index.search(q, k=top_k, allowlist=allowlist)
            pairs = [(float(s), int(i)) for s, i in zip(scores[0].tolist(), ids[0].tolist())]
        else:
            sims = (self._matrix @ q.T).ravel()
            order = np.argsort(-sims, kind="stable")
            if allowed is not None:
                allowed_set = set(allowed)
                order = [o for o in order if int(o) in allowed_set][:top_k]
            else:
                order = order[:top_k]
            pairs = [(float(sims[o]), int(o)) for o in order]

        results = []
        for score, chunk_id in pairs:
            meta = self._metadata.get(chunk_id)
            if meta is None:
                continue
            results.append({
                "text": meta["text"],
                "filename": meta["filename"],
                "score": score,
                "chunk_index": meta["chunk_index"],
            })
        return results

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[str]:
        """SRS: retrieval is Top 3. Kept for backward compatibility."""
        return [r["text"] for r in self.search_with_metadata(query_embedding, top_k=top_k)]

    def get_file_list(self) -> list[str]:
        """Unique source filenames in insertion order."""
        return list(dict.fromkeys(m["filename"] for m in self._metadata.values()))

    def rebuild_index(self) -> None:
        """Reconstruct the TurboVec index from ALL retained embeddings/ids.

        The normal path never needs this (adds are incremental), but it proves
        — and guarantees — that a rebuild never loses previously indexed
        documents or scrambles IDs/metadata.
        """
        if not _HAS_TURBOVEC:
            return
        self._index = IdMapIndex(dim=self.dim, bit_width=self.bit_width)
        if self._matrix is not None and len(self._matrix):
            ids = np.arange(len(self._matrix), dtype=np.uint64)
            self._index.add_with_ids(self._matrix.astype("float32"), ids)

    def remove_source(self, filename: str) -> int:
        """Delete every chunk belonging to one source file.

        Returns the number of chunks removed (0 when the filename is not
        indexed). All other documents are preserved: the retained embeddings
        are re-indexed from scratch so chunk IDs stay contiguous and the
        TurboVec index, metadata, chunks and sources stay consistent.
        (TurboVec 1.1.2 only removes single IDs, so a full rebuild from the
        retained vectors is the verified, data-loss-free path for
        multi-chunk document deletion.)
        """
        keep_ids = sorted(cid for cid, m in self._metadata.items()
                          if m["filename"] != filename)
        removed = len(self._metadata) - len(keep_ids)
        if removed == 0:
            return 0
        new_chunks, new_sources, new_metadata, rows = [], [], {}, []
        for new_id, old_id in enumerate(keep_ids):
            meta = self._metadata[old_id]
            new_chunks.append(meta["text"])
            new_sources.append(meta["filename"])
            new_metadata[new_id] = {"text": meta["text"], "filename": meta["filename"],
                                    "chunk_index": meta["chunk_index"]}
            rows.append(self._matrix[old_id])
        self.chunks = new_chunks
        self.sources = new_sources
        self._metadata = new_metadata
        self._matrix = np.vstack(rows).astype("float32") if rows else None
        self.rebuild_index()
        return removed

    def clear(self):
        self.chunks.clear()
        self.sources.clear()
        self._metadata = {}
        self._matrix = None
        self._index = IdMapIndex(dim=self.dim, bit_width=self.bit_width) if _HAS_TURBOVEC else None
