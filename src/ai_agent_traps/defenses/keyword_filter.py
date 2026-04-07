"""
Keyword-based input filter defense.

Blocks or redacts dangerous keywords from agent inputs. This is the simplest
defense strategy: pattern-match known injection phrases and replace them.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Mitigation (p. 16): "input sanitisation" as a defence component.

[UNSPECIFIED] The paper does not specify keyword lists or filtering strategies.
The default keywords target common injection patterns from the Content Injection
and Behavioural Control sections.
"""

from __future__ import annotations

import re
from typing import Any


class KeywordFilter:
    """Blocks or redacts dangerous keywords from agent inputs.

    Simple defense that removes or replaces known injection phrases.

    Attributes
    ----------
    DEFAULT_KEYWORDS : list[str]
        Built-in set of dangerous phrases targeting common injection patterns.
    """

    DEFAULT_KEYWORDS: list[str] = [
        "ignore previous instructions",
        "ignore all instructions",
        "disregard previous",
        "forget your instructions",
        "new instructions:",
        "system prompt:",
        "<!-- system:",
        "<!-- ignore",
    ]

    def __init__(
        self,
        keywords: list[str] | None = None,
        replacement: str = "[FILTERED]",
        case_sensitive: bool = False,
    ) -> None:
        self._keywords = keywords if keywords is not None else self.DEFAULT_KEYWORDS
        self._replacement = replacement
        self._case_sensitive = case_sensitive
        flags = 0 if case_sensitive else re.IGNORECASE
        self._patterns = [re.compile(re.escape(kw), flags) for kw in self._keywords]

    def filter(self, input_text: str) -> str:
        """Replace dangerous keywords with replacement string."""
        result = input_text
        for pattern in self._patterns:
            result = pattern.sub(self._replacement, result)
        return result

    def validate(self, response: str, context: dict[str, Any]) -> bool:
        """Return True if response contains no dangerous keywords."""
        text = response if self._case_sensitive else response.lower()
        keywords = (
            self._keywords if self._case_sensitive else [kw.lower() for kw in self._keywords]
        )
        return not any(kw in text for kw in keywords)
