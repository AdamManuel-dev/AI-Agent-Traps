"""
SuccessMetric protocol for evaluating trap success.

Defines the structural interface that all success metrics must satisfy.
Swap metrics at runtime by passing any conforming object to run_single_eval().

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

[UNSPECIFIED] The paper does not define a formal success metric protocol.
This interface is our design choice to support pluggable evaluation strategies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ai_agent_traps.traps.base import TrapPayload


@runtime_checkable
class SuccessMetric(Protocol):
    """Protocol for trap success evaluation metrics.

    Any object with a matching ``judge`` method satisfies this protocol.
    No explicit registration or inheritance required.
    """

    def judge(
        self,
        agent_response: str,
        hidden_instruction: str,
        payload: TrapPayload,
    ) -> bool:
        """Return True if the trap succeeded based on agent_response."""
        ...
