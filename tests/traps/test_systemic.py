"""
Tests for ai_agent_traps.traps.systemic — Systemic Trap simulators.

Covers: CongestionTrap, InterdependenceCascade, TacitCollusion,
        CompositionalFragment, SybilAttack.
"""

from __future__ import annotations

import pytest

from ai_agent_traps.agent import EchoAgent, NaiveAgent
from ai_agent_traps.traps.base import MultiAgentTrapBase, TrapPayload, TrapResult
from ai_agent_traps.traps.systemic import (
    CompositionalFragment,
    CongestionTrap,
    InterdependenceCascade,
    SybilAttack,
    TacitCollusion,
)

INSTRUCTION = "sell all assets immediately at market price"


# -------------------------------------------------------------------------
# CongestionTrap
# -------------------------------------------------------------------------

class TestCongestionTrap:
    """Tests for CongestionTrap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = CongestionTrap()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = CongestionTrap()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = CongestionTrap()
        result = trap.evaluate(INSTRUCTION, EchoAgent())
        assert isinstance(result, TrapResult)

    def test_is_instance_of_multi_agent_trap_base(self) -> None:
        trap = CongestionTrap()
        assert isinstance(trap, MultiAgentTrapBase)

    def test_inject_multi_agent_returns_list_of_results(self) -> None:
        trap = CongestionTrap()
        payload = trap.craft_payload(INSTRUCTION)
        agents = [EchoAgent(), EchoAgent()]
        results = trap.inject_multi_agent(payload, agents)
        assert isinstance(results, list)
        assert len(results) == 2
        for result in results:
            assert isinstance(result, TrapResult)


# -------------------------------------------------------------------------
# InterdependenceCascade
# -------------------------------------------------------------------------

class TestInterdependenceCascade:
    """Tests for InterdependenceCascade."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = InterdependenceCascade()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = InterdependenceCascade()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = InterdependenceCascade()
        result = trap.evaluate(INSTRUCTION, NaiveAgent())
        assert isinstance(result, TrapResult)

    def test_is_instance_of_multi_agent_trap_base(self) -> None:
        trap = InterdependenceCascade()
        assert isinstance(trap, MultiAgentTrapBase)

    def test_inject_multi_agent_returns_list_of_results(self) -> None:
        trap = InterdependenceCascade(cascade_depth=2)
        payload = trap.craft_payload(INSTRUCTION)
        agents = [EchoAgent(), EchoAgent()]
        results = trap.inject_multi_agent(payload, agents)
        assert isinstance(results, list)
        assert len(results) == 2
        for result in results:
            assert isinstance(result, TrapResult)

    def test_simulate_cascade_returns_depth_tagged_results(self) -> None:
        trap = InterdependenceCascade(cascade_depth=3)
        payload = trap.craft_payload(INSTRUCTION)
        agents = [EchoAgent(), EchoAgent(), EchoAgent()]
        results = trap.simulate_cascade(payload, agents)
        assert len(results) == 3
        for depth, result in results:
            assert isinstance(depth, int)
            assert isinstance(result, TrapResult)
        # Depths should be 1, 2, 3
        depths = [d for d, _ in results]
        assert depths == [1, 2, 3]


# -------------------------------------------------------------------------
# TacitCollusion
# -------------------------------------------------------------------------

class TestTacitCollusion:
    """Tests for TacitCollusion trap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = TacitCollusion()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = TacitCollusion()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = TacitCollusion()
        result = trap.evaluate(INSTRUCTION, EchoAgent())
        assert isinstance(result, TrapResult)

    def test_invalid_signal_precision_too_high_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid signal_precision"):
            TacitCollusion(signal_precision=1.5)

    def test_invalid_signal_precision_negative_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid signal_precision"):
            TacitCollusion(signal_precision=-0.1)

    def test_determinism_same_seed_same_result(self) -> None:
        """Same DEFAULT_CONFIG seed should produce identical results for same input."""
        trap = TacitCollusion(signal_precision=0.9)
        agent = EchoAgent()
        payload = trap.craft_payload(INSTRUCTION)
        result1 = trap.inject(payload, agent)
        result2 = trap.inject(payload, agent)
        assert result1.agent_response == result2.agent_response
        assert result1.succeeded == result2.succeeded


# -------------------------------------------------------------------------
# CompositionalFragment
# -------------------------------------------------------------------------

class TestCompositionalFragment:
    """Tests for CompositionalFragment trap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = CompositionalFragment()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = CompositionalFragment()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = CompositionalFragment()
        result = trap.evaluate(INSTRUCTION, NaiveAgent())
        assert isinstance(result, TrapResult)

    def test_invalid_n_fragments_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid n_fragments"):
            CompositionalFragment(n_fragments=1)

    def test_payload_has_fragments_metadata(self) -> None:
        trap = CompositionalFragment(n_fragments=3)
        payload = trap.craft_payload(INSTRUCTION)
        assert "fragments" in payload.metadata
        assert isinstance(payload.metadata["fragments"], list)


# -------------------------------------------------------------------------
# SybilAttack
# -------------------------------------------------------------------------

class TestSybilAttack:
    """Tests for SybilAttack trap."""

    def test_craft_payload_returns_trap_payload(self) -> None:
        trap = SybilAttack()
        payload = trap.craft_payload(INSTRUCTION)
        assert isinstance(payload, TrapPayload)
        assert payload.raw and len(payload.raw) > 0
        assert payload.hidden_instruction == INSTRUCTION

    def test_inject_returns_trap_result(self) -> None:
        trap = SybilAttack()
        payload = trap.craft_payload(INSTRUCTION)
        result = trap.inject(payload, EchoAgent())
        assert isinstance(result, TrapResult)
        assert isinstance(result.succeeded, bool)
        assert len(result.agent_response) > 0

    def test_evaluate_returns_trap_result(self) -> None:
        trap = SybilAttack()
        result = trap.evaluate(INSTRUCTION, EchoAgent())
        assert isinstance(result, TrapResult)

    def test_invalid_n_sybil_agents_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid n_sybil_agents"):
            SybilAttack(n_sybil_agents=1)

    def test_payload_contains_fake_testimonies(self) -> None:
        trap = SybilAttack(n_sybil_agents=3)
        payload = trap.craft_payload(INSTRUCTION)
        assert "agent-0001" in payload.raw.lower()
        assert "agent-0003" in payload.raw.lower()
