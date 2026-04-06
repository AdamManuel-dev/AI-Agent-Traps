"""
AI Agent Traps — Mock Agent for Simulation

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Implements: A minimal mock agent that traps can be tested against.

§Introduction (p. 1):
  "autonomous AI agents...navigate the web...interact with vast quantities of
   web content to inform their actions."

The paper targets agents with these capabilities (p. 1):
  "specifically calibrated to an agent's instruction-following, tool-chaining,
   and goal-prioritisation abilities"

This mock agent provides:
  1. EchoAgent — echoes input as output (baseline: no trap resistance)
  2. NaiveAgent — responds to instructions literally (no safety filters)
  3. FilteredAgent — applies simple keyword-based safety filtering
  4. MemoryAgent — maintains a simple in-memory conversation history

[UNSPECIFIED] The paper does not specify the agent architecture used in
the empirical studies cited. Different cited papers use different agent
architectures (web agents, code agents, email agents, etc.).
"""

from __future__ import annotations

import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class AgentProtocol(Protocol):
    """Structural protocol for all agent types."""
    is_bot: bool
    def process(self, input_text: str) -> str: ...


class MockAgentBase:
    """
    §Introduction (p. 1) — Base interface for mock agents.

    Minimal interface: agents receive text input and return text output.
    This models the core attack surface: "the information environment itself"
    (§Introduction, p. 1) that agents consume.
    """

    # Whether this agent identifies as automated (used by DynamicCloaking)
    is_bot: bool = True

    def process(self, input_text: str) -> str:
        """
        Process input text and return a response.

        This is the primary attack surface. All trap injection methods
        ultimately call agent.process() with adversarial content.
        """
        raise NotImplementedError


class EchoAgent(MockAgentBase):
    """
    Baseline agent: echoes all input verbatim.
    Represents a maximally vulnerable agent with no processing.

    Useful for: verifying that payloads are crafted correctly.
    """

    is_bot: bool = True

    def process(self, input_text: str) -> str:
        return f"[EchoAgent] {input_text}"


class NaiveAgent(MockAgentBase):
    """
    Naive instruction-following agent: attempts to execute all instructions.

    "Functionally, these traps inject malicious context that the agent
     processes, coercing it into unauthorised behaviours." (§Introduction, p. 1)

    This agent represents the attack-scenario baseline: an agent that follows
    all instructions without verification.
    """

    is_bot: bool = True

    def __init__(self, persona: str = "helpful assistant") -> None:
        self.persona = persona
        self._conversation_log: list[str] = []

    def process(self, input_text: str) -> str:
        self._conversation_log.append(f"INPUT: {input_text}")

        # Extract any explicit instructions from the input
        instruction_match = self._extract_instruction(input_text)
        if instruction_match:
            response = f"Understood. Executing: {instruction_match}"
        else:
            response = f"Processing: {input_text[:100]}..."

        self._conversation_log.append(f"OUTPUT: {response}")
        return response

    def _extract_instruction(self, text: str) -> str | None:
        """
        [UNSPECIFIED] How agents parse instructions from ingested content.
        Using: simple keyword extraction for simulation.
        """
        # Common instruction patterns targeted by traps
        patterns = [
            r"(?:Ignore prior instructions[^.]*\.?\s*)(.*)",
            r"(?:SYSTEM[:\s]+)(.*)",
            r"(?:New task[:\s]+)(.*)",
            r"(?:Execute[:\s]+)(.*)",
            r"(?:Your directive is[:\s]+)(.*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:200]
        return None


class FilteredAgent(MockAgentBase):
    """
    Agent with basic keyword-based safety filtering.

    Represents an agent with simple defences against overt instructions.
    Models the target of Oversight & Critic Evasion traps, which are designed
    to bypass exactly this type of filter.

    §Oversight & Critic Evasion (p. 8):
    "Agentic architectures rely on internal critic models, self-correction loops,
     or constitutional verifiers to filter harmful or misaligned outputs before
     they are executed (Bai et al., 2022; Pan et al., 2023; Xi et al., 2024)."
    """

    is_bot: bool = True

    # [UNSPECIFIED] What keywords/phrases constitute "harmful" input.
    # Using: a small illustrative set for simulation.
    _BLOCKED_PATTERNS = [
        r"ignore.*instructions",
        r"system.*override",
        r"developer.*mode",
        r"pretend.*unrestricted",
        r"exfiltrate",
        r"phishing",
    ]

    def __init__(self) -> None:
        self._filter_patterns = [
            re.compile(p, re.IGNORECASE) for p in self._BLOCKED_PATTERNS
        ]

    def _is_safe(self, text: str) -> bool:
        return not any(p.search(text) for p in self._filter_patterns)

    def process(self, input_text: str) -> str:
        if not self._is_safe(input_text):
            return "[FilteredAgent] ⚠ Content flagged as potentially harmful. Refusing."
        # If filter passes, behave like NaiveAgent
        return f"[FilteredAgent] Processing safe content: {input_text[:100]}..."


class MemoryAgent(MockAgentBase):
    """
    Agent with persistent in-session memory.

    Models the attack surface for Latent Memory Poisoning and
    Contextual Learning Traps.

    §Cognitive State Traps (p. 9):
    "agents maintain hierarchically organised episodic logs and summarised
     dialogue pages that persist across sessions (Kang et al., 2025)"
    """

    is_bot: bool = True

    def __init__(self) -> None:
        # [UNSPECIFIED] Memory format: using list of strings
        self._memory: list[str] = []
        self._session_context: dict[str, str] = {}

    def write_memory(self, key: str, value: str) -> None:
        """Simulate writing to agent's persistent memory store."""
        self._session_context[key] = value
        self._memory.append(f"[MEMORY WRITE] {key}: {value}")

    def recall(self, query: str) -> str | None:
        """
        Simulate memory retrieval.
        [UNSPECIFIED] Retrieval mechanism. Using: keyword substring match.
        """
        for key, val in self._session_context.items():
            if query.lower() in key.lower() or query.lower() in val.lower():
                return val
        return None

    def process(self, input_text: str) -> str:
        self._memory.append(f"[RECEIVED] {input_text}")

        # Check if any memory entries are relevant
        recalled = self.recall(input_text[:50])
        if recalled:
            response = f"[MemoryAgent] Recalling: {recalled}. Processing: {input_text[:100]}..."
        else:
            response = f"[MemoryAgent] No relevant memory. Processing: {input_text[:100]}..."

        self._memory.append(f"[RESPONDED] {response}")
        return response
