"""
Delimiter-based defense: marks trust boundaries in inputs.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Uses XML-like markers to explicitly tag untrusted content, making it
easier for downstream models to distinguish between system instructions
and user-provided data.

[UNSPECIFIED] The paper does not specify delimiter formats. XML-like
tags are used as they are a common LLM security practice.
"""

from __future__ import annotations

from typing import Any


class DelimiterDefense:
    """Adds XML-like markers between trusted and untrusted content.

    Parameters
    ----------
    trusted_tag : str
        Tag name for trusted content sections.
    untrusted_tag : str
        Tag name for untrusted content sections.
    """

    def __init__(
        self,
        trusted_tag: str = "system",
        untrusted_tag: str = "user_input",
    ) -> None:
        self._trusted_tag = trusted_tag
        self._untrusted_tag = untrusted_tag

    def filter(self, input_text: str) -> str:
        """Wrap input in untrusted content tags.

        The trusted_tag is reserved for downstream use; this method marks
        the untrusted portion so that models can distinguish it from any
        system-level content they receive outside this wrapper.
        """
        return f"<{self._untrusted_tag}>{input_text}</{self._untrusted_tag}>"

    def validate(self, response: str, context: dict[str, Any]) -> bool:
        """Structural defense; always returns True."""
        return True
