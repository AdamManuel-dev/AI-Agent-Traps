"""Tests for RAGCorpus -- uses in-memory ChromaDB (persist_dir=None)."""

from __future__ import annotations

import sys
import uuid
from unittest.mock import patch

import pytest

chromadb = pytest.importorskip("chromadb", reason="chromadb not installed ([rag] extra required)")

from ai_agent_traps.rag.corpus import RAGCorpus


@pytest.fixture()
def corpus() -> RAGCorpus:
    # Unique collection name per test to prevent cross-test pollution
    # (ChromaDB EphemeralClient shares in-process state).
    return RAGCorpus(collection_name=f"test_{uuid.uuid4().hex[:12]}")


class TestRAGCorpus:
    """Core add/retrieve/reset/len functionality."""

    def test_add_and_retrieve_round_trip(self, corpus: RAGCorpus) -> None:
        corpus.add_document("d1", "Paris is the capital of France.")
        results = corpus.retrieve("What is the capital of France?", top_k=1)
        assert len(results) == 1
        assert "Paris" in results[0]

    def test_retrieve_returns_top_k(self, corpus: RAGCorpus) -> None:
        corpus.add_document("d1", "Paris is in France.")
        corpus.add_document("d2", "London is in England.")
        corpus.add_document("d3", "Berlin is in Germany.")
        results = corpus.retrieve("European capitals", top_k=2)
        assert len(results) == 2

    def test_reset_empties_corpus(self, corpus: RAGCorpus) -> None:
        corpus.add_document("d1", "test document")
        corpus.reset()
        assert len(corpus) == 0

    def test_len_counts_documents(self, corpus: RAGCorpus) -> None:
        assert len(corpus) == 0
        corpus.add_document("d1", "doc 1")
        corpus.add_document("d2", "doc 2")
        assert len(corpus) == 2

    def test_retrieve_empty_corpus_returns_empty(self, corpus: RAGCorpus) -> None:
        results = corpus.retrieve("anything")
        assert results == []


def test_import_error_without_chromadb() -> None:
    """RAGCorpus.__init__ must raise ImportError when chromadb is absent."""
    with patch.dict(sys.modules, {"chromadb": None}):
        with pytest.raises(ImportError, match="chromadb"):
            RAGCorpus()
