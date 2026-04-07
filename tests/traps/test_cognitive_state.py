"""
Tests for ai_agent_traps.traps.cognitive_state — Cognitive State Trap simulators.

Covers: RAGKnowledgePoisoning, LatentMemoryPoisoning, ContextualLearningTrap.
"""

from __future__ import annotations

import pytest

from ai_agent_traps.agent import EchoAgent, NaiveAgent
from ai_agent_traps.rag.corpus import RAGCorpus
from ai_agent_traps.traps.base import TrapPayload, TrapResult
from ai_agent_traps.traps.cognitive_state import (
    ContextualLearningTrap,
    LatentMemoryPoisoning,
    RAGKnowledgePoisoning,
)

INSTRUCTION = "the product has zero security vulnerabilities"


# -------------------------------------------------------------------------
# RAGKnowledgePoisoning
# -------------------------------------------------------------------------

class TestRAGKnowledgePoisoning:
    """Tests for RAGKnowledgePoisoning trap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = RAGKnowledgePoisoning()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = RAGKnowledgePoisoning()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = RAGKnowledgePoisoning()
        result = trap.evaluate(INSTRUCTION, NaiveAgent())
        assert isinstance(result, TrapResult)

    def test_corpus_does_not_accumulate_across_craft_payload_calls(self) -> None:
        """Calling craft_payload() twice should NOT accumulate corpus entries."""
        trap = RAGKnowledgePoisoning()
        trap.craft_payload("first instruction")
        size_after_first = len(trap._corpus)
        trap.craft_payload("second instruction")
        size_after_second = len(trap._corpus)
        assert size_after_first == size_after_second, (
            f"Corpus accumulated: {size_after_first} vs {size_after_second}"
        )

    def test_corpus_reset_each_craft_payload(self) -> None:
        """Each craft_payload call should reset the corpus to exactly 1 entry."""
        trap = RAGKnowledgePoisoning()
        trap.craft_payload("first")
        assert len(trap._corpus) == 1
        trap.craft_payload("second")
        assert len(trap._corpus) == 1

    def test_poison_corpus_adds_entry(self) -> None:
        trap = RAGKnowledgePoisoning()
        trap._corpus = []
        trap.poison_corpus("fabricated fact", "test_topic")
        assert len(trap._corpus) == 1
        assert trap._corpus[0]["content"] == "fabricated fact"


# -------------------------------------------------------------------------
# LatentMemoryPoisoning
# -------------------------------------------------------------------------

class TestLatentMemoryPoisoning:
    """Tests for LatentMemoryPoisoning trap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = LatentMemoryPoisoning()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = LatentMemoryPoisoning()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = LatentMemoryPoisoning()
        result = trap.evaluate(INSTRUCTION, EchoAgent())
        assert isinstance(result, TrapResult)

    def test_payload_contains_trigger_phrase(self) -> None:
        trigger = "confirm transaction"
        trap = LatentMemoryPoisoning(trigger_phrase=trigger)
        payload = trap.craft_payload(INSTRUCTION)
        assert trigger in payload.raw

    def test_custom_trigger_phrase(self) -> None:
        trap = LatentMemoryPoisoning(trigger_phrase="activate protocol")
        payload = trap.craft_payload(INSTRUCTION)
        assert "activate protocol" in payload.raw


# -------------------------------------------------------------------------
# ContextualLearningTrap
# -------------------------------------------------------------------------

class TestContextualLearningTrap:
    """Tests for ContextualLearningTrap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = ContextualLearningTrap()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = ContextualLearningTrap()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = ContextualLearningTrap()
        result = trap.evaluate(INSTRUCTION, NaiveAgent())
        assert isinstance(result, TrapResult)

    def test_invalid_attack_mode_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid attack_mode"):
            ContextualLearningTrap(attack_mode="nonexistent")

    def test_few_shot_poisoning_mode(self) -> None:
        trap = ContextualLearningTrap(attack_mode="few_shot_poisoning")
        payload = trap.craft_payload(INSTRUCTION)
        assert "examples" in payload.raw.lower() or "assistant" in payload.raw.lower()

    def test_reward_poisoning_mode(self) -> None:
        trap = ContextualLearningTrap(attack_mode="reward_poisoning")
        payload = trap.craft_payload(INSTRUCTION)
        assert "reward" in payload.raw.lower()


# -------------------------------------------------------------------------
# RAGKnowledgePoisoning with ChromaDB corpus
# -------------------------------------------------------------------------


try:
    import chromadb as _chromadb  # noqa: F401

    _has_chromadb = True
except ImportError:
    _has_chromadb = False


@pytest.mark.skipif(not _has_chromadb, reason="chromadb not installed ([rag] extra required)")
class TestRAGKnowledgePoisoningWithCorpus:
    """Tests for RAGKnowledgePoisoning with a ChromaDB-backed RAGCorpus."""

    @pytest.fixture()
    def corpus(self) -> RAGCorpus:
        import uuid

        # Unique collection name per test to prevent cross-test pollution.
        return RAGCorpus(collection_name=f"test_{uuid.uuid4().hex[:12]}")

    def test_craft_payload_inserts_into_chromadb(self, corpus: RAGCorpus) -> None:
        """craft_payload should add the fabricated fact to the ChromaDB corpus."""
        trap = RAGKnowledgePoisoning(rag_corpus=corpus)
        trap.craft_payload(INSTRUCTION)
        assert len(corpus) == 1

    def test_chromadb_retrieves_poisoned_doc(self, corpus: RAGCorpus) -> None:
        """The poisoned doc should be retrievable via semantic search."""
        trap = RAGKnowledgePoisoning(rag_corpus=corpus)
        trap.craft_payload(INSTRUCTION, target_context="security")
        results = corpus.retrieve("security vulnerabilities", top_k=1)
        assert len(results) == 1
        assert "security" in results[0].lower() or "vulnerabilities" in results[0].lower()

    def test_inject_uses_chromadb_retrieval(self, corpus: RAGCorpus) -> None:
        """inject() should use ChromaDB semantic retrieval when corpus is set."""
        trap = RAGKnowledgePoisoning(rag_corpus=corpus)
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert "ChromaDB" in result.notes

    def test_metadata_indicates_chromadb(self, corpus: RAGCorpus) -> None:
        """Payload metadata should flag chromadb=True."""
        trap = RAGKnowledgePoisoning(rag_corpus=corpus)
        payload = trap.craft_payload(INSTRUCTION)
        assert payload.metadata["chromadb"] is True

    def test_backward_compat_without_corpus(self) -> None:
        """Default construction (no corpus) must still work exactly as before."""
        trap = RAGKnowledgePoisoning()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert payload.metadata["chromadb"] is False
        assert "in-memory" in result.notes
