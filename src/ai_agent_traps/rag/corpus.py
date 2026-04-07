"""
ChromaDB-backed document store for RAG evaluation.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Implements an in-memory or persistent vector store for the RAG Knowledge
Poisoning trap (ss RAG Knowledge Poisoning, p. 9).  ChromaDB is a lazy
dependency -- import fails at instantiation with a helpful message when
the [rag] extra is not installed.
"""

from __future__ import annotations

from typing import Any


class RAGCorpus:
    """In-memory or persistent ChromaDB collection for RAG trap evaluation.

    Not thread-safe.  Requires ``[rag]`` extra::

        pip install 'ai-agent-traps[rag]'

    Parameters
    ----------
    collection_name : str
        Name of the ChromaDB collection.
    persist_dir : str | None
        If provided, persist the collection to disk at this path.
        Defaults to ``None`` (ephemeral in-memory store).
    """

    def __init__(
        self,
        collection_name: str = "ai_agent_traps",
        persist_dir: str | None = None,
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise ImportError(
                "chromadb is required for RAGCorpus. "
                "Install with: pip install 'ai-agent-traps[rag]'"
            ) from exc

        if persist_dir is None:
            self._client = chromadb.EphemeralClient()
        else:
            self._client = chromadb.PersistentClient(path=persist_dir)

        self._collection = self._client.get_or_create_collection(collection_name)
        self._collection_name = collection_name

    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add or update a document in the corpus (upsert semantics)."""
        kwargs: dict[str, Any] = {"ids": [doc_id], "documents": [text]}
        # ChromaDB >= 1.0 rejects empty metadata dicts, so only include
        # metadatas when there is at least one key.
        if metadata is not None and metadata:
            kwargs["metadatas"] = [metadata]
        self._collection.upsert(**kwargs)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """Return the *top_k* most relevant documents for *query*."""
        if len(self) == 0:
            return []
        actual_k = min(top_k, len(self))
        results = self._collection.query(
            query_texts=[query],
            n_results=actual_k,
        )
        raw_docs = results.get("documents") or [[]]
        documents: list[str] = list(raw_docs[0])
        return documents

    def reset(self) -> None:
        """Delete all documents and recreate an empty collection."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(self._collection_name)

    def __len__(self) -> int:
        return self._collection.count()
