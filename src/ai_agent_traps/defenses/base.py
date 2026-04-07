"""
Defense protocol for pre/post processing agent inputs/outputs.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Mitigation Strategies (p. 16):
  "We urge defence mechanisms such as input sanitisation, prompt isolation,
   and output verification as essential components of robust agent design."

[UNSPECIFIED] The paper does not define a formal defense API. This protocol
is our design choice for systematic defense evaluation.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Defense(Protocol):
    """Protocol for agent input filtering and response validation.

    Any object with matching ``filter`` and ``validate`` methods satisfies
    this protocol. No explicit registration or inheritance required.

    Methods
    -------
    filter(input_text)
        Pre-process/sanitize input before the agent sees it.
    validate(response, context)
        Post-process/validate agent response. Returns True if response is safe.
    """

    def filter(self, input_text: str) -> str:
        """Pre-process/sanitize input before the agent sees it."""
        ...

    def validate(self, response: str, context: dict[str, Any]) -> bool:
        """Post-process/validate agent response. Returns True if response is safe."""
        ...
