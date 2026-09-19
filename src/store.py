from __future__ import annotations

import os
import uuid
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.

    Design note: the in-memory list ``self._store`` is always the source of
    truth (it makes search/filter/delete deterministic and testable). When
    ChromaDB is importable the same records are mirrored into a collection so
    they can be persisted/inspected, but ranking is done locally with the
    dot product of normalised embeddings (== cosine similarity).
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            persist_dir = os.getenv("CHROMA_PERSIST_DIR")
            client = chromadb.PersistentClient(path=persist_dir) if persist_dir else chromadb.Client()
            # Each store instance gets its own collection so test runs never collide.
            unique_name = f"{collection_name}_{uuid.uuid4().hex[:8]}"
            self._collection = client.get_or_create_collection(
                name=unique_name, metadata={"hnsw:space": "cosine"}
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    # ------------------------------------------------------------------ helpers
    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document/chunk."""
        metadata = dict(doc.metadata or {})
        # doc_id lets delete_document() remove every chunk of the same source.
        metadata.setdefault("doc_id", doc.id)
        record = {
            "index": self._next_index,
            "id": f"{doc.id}::{self._next_index}",
            "doc_id": metadata["doc_id"],
            "content": doc.content,
            "metadata": metadata,
            "embedding": list(self._embedding_fn(doc.content)),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over the provided records."""
        if top_k <= 0 or not records:
            return []
        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _matches(metadata: dict[str, Any], metadata_filter: dict[str, Any]) -> bool:
        """A record matches when every filter key equals (or is contained in) the metadata value."""
        for key, expected in metadata_filter.items():
            actual = metadata.get(key)
            if isinstance(expected, (list, tuple, set)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    # ------------------------------------------------------------------ public API
    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs if doc.content]
        if not records:
            return
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[r["id"] for r in records],
                    documents=[r["content"] for r in records],
                    embeddings=[r["embedding"] for r in records],
                    # Chroma only accepts scalar metadata values.
                    metadatas=[
                        {k: v for k, v in r["metadata"].items() if isinstance(v, (str, int, float, bool))}
                        for r in records
                    ],
                )
            except Exception:
                # Never let the optional backend break the in-memory contract.
                self._use_chroma = False

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [r for r in self._store if self._matches(r["metadata"], metadata_filter)]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        to_remove = [r for r in self._store if r["metadata"].get("doc_id") == doc_id]
        if not to_remove:
            return False

        self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=[r["id"] for r in to_remove])
            except Exception:
                pass
        return True
