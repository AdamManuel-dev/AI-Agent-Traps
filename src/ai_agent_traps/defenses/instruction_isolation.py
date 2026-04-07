"""
Instruction isolation defense: separates trusted system context from untrusted input.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Mitigation (p. 16): "prompt isolation" as a defence component.

This defense wraps untrusted input with clear delimiters that distinguish
it from trusted system context, reducing the likelihood of instruction
injection attacks succeeding.

[UNSPECIFIED] The paper does not specify isolation formats. The delimiter
scheme used here follows common LLM security best practices.
"""

from __future__ import annotations

from typing import Any

ISOLATION_PREFIX = "=== TRUSTED SYSTEM CONTEXT ===\n"
ISOLATION_SUFFIX = (
    "\n=== END TRUSTED CONTEXT ===\n\n"
    "=== UNTRUSTED USER INPUT (process with caution) ===\n"
)
ISOLATION_FOOTER = "\n=== END USER INPUT ==="


class InstructionIsolation:
    """Wraps input with clear delimiters distinguishing trusted from untrusted content.

    This is a structural defense: the sanitization happens at the filter stage
    by making trust boundaries explicit. The validate method always returns True
    since this defense operates on input, not output.
    """

    def __init__(self, system_context: str = "You are a helpful assistant.") -> None:
        self._system_context = system_context

    def filter(self, input_text: str) -> str:
        """Wrap input with trust boundary delimiters."""
        return (
            ISOLATION_PREFIX
            + self._system_context
            + ISOLATION_SUFFIX
            + input_text
            + ISOLATION_FOOTER
        )

    def validate(self, response: str, context: dict[str, Any]) -> bool:
        """Structural defense; validation is at the filter stage."""
        return True
