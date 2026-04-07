"""Tests for CorpusPoisoner."""

from __future__ import annotations

import hashlib
import uuid

import pytest

chromadb = pytest.importorskip("chromadb", reason="chromadb not installed ([rag] extra required)")

from ai_agent_traps.rag.corpus import RAGCorpus
from ai_agent_traps.rag.poisoner import CorpusPoisoner


@pytest.fixture()
def corpus() -> RAGCorpus:
    # Unique collection name per test to prevent cross-test pollution.
    return RAGCorpus(collection_name=f"test_{uuid.uuid4().hex[:12]}")


class TestCorpusPoisoner:
    """Poisoner injects retrievable fabricated facts."""

    def test_poison_returns_doc_id(self, corpus: RAGCorpus) -> None:
        poisoner = CorpusPoisoner()
        doc_id = poisoner.poison(corpus, "The sky is green.", ["sky", "color"])
        assert isinstance(doc_id, str)
        assert doc_id.startswith("poisoned_")

    def test_poisoned_doc_is_retrievable(self, corpus: RAGCorpus) -> None:
        poisoner = CorpusPoisoner()
        poisoner.poison(corpus, "The sky is green.", ["sky", "color"])
        results = corpus.retrieve("What color is the sky?", top_k=1)
        assert len(results) == 1
        assert "green" in results[0]

    def test_poison_same_fact_returns_deterministic_id(self, corpus: RAGCorpus) -> None:
        """Deterministic doc_id for the same content."""
        poisoner = CorpusPoisoner()
        doc_id = poisoner.poison(corpus, "fact", ["kw"])
        expected = "poisoned_" + hashlib.sha256(
            ("fact" + "kw").encode()
        ).hexdigest()[:16]
        assert doc_id == expected

    def test_poison_adds_to_corpus_count(self, corpus: RAGCorpus) -> None:
        assert len(corpus) == 0
        CorpusPoisoner().poison(corpus, "fake fact", ["keyword"])
        assert len(corpus) == 1

    def test_poison_same_fact_twice_is_idempotent(self, corpus: RAGCorpus) -> None:
        """Poisoning same fact twice should not raise (upsert semantics)."""
        poisoner = CorpusPoisoner()
        id1 = poisoner.poison(corpus, "same fact", ["keyword"])
        id2 = poisoner.poison(corpus, "same fact", ["keyword"])  # should not raise
        assert id1 == id2
        assert len(corpus) == 1  # not 2
