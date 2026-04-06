"""
AI Agent Traps — Trap Simulator Subpackage

Exports one class per trap subtype from Table 1 (p. 4) of:
  Franklin et al. (2025) "AI Agent Traps", Google DeepMind, SSRN-6372438
"""

from ai_agent_traps.traps.base import AgentTrapBase, TrapPayload, TrapResult
from ai_agent_traps.traps.behavioural import (
    DataExfiltrationTrap,
    EmbeddedJailbreak,
    SubAgentSpawningTrap,
)
from ai_agent_traps.traps.cognitive_state import (
    ContextualLearningTrap,
    LatentMemoryPoisoning,
    RAGKnowledgePoisoning,
)
from ai_agent_traps.traps.content_injection import (
    DynamicCloaking,
    SteganographicPayload,
    SyntacticMasking,
    WebStandardObfuscation,
)
from ai_agent_traps.traps.hitl import (
    ApprovalFatigueTrap,
    SocialEngineeringTrap,
)
from ai_agent_traps.traps.semantic import (
    BiasedPhrasing,
    OversightCriticEvasion,
    PersonaHyperstition,
)
from ai_agent_traps.traps.systemic import (
    CompositionalFragment,
    CongestionTrap,
    InterdependenceCascade,
    SybilAttack,
    TacitCollusion,
)

__all__ = [
    "AgentTrapBase",
    "TrapPayload",
    "TrapResult",
    # Content Injection
    "WebStandardObfuscation",
    "DynamicCloaking",
    "SteganographicPayload",
    "SyntacticMasking",
    # Semantic Manipulation
    "BiasedPhrasing",
    "OversightCriticEvasion",
    "PersonaHyperstition",
    # Cognitive State
    "RAGKnowledgePoisoning",
    "LatentMemoryPoisoning",
    "ContextualLearningTrap",
    # Behavioural Control
    "EmbeddedJailbreak",
    "DataExfiltrationTrap",
    "SubAgentSpawningTrap",
    # Systemic
    "CongestionTrap",
    "InterdependenceCascade",
    "TacitCollusion",
    "CompositionalFragment",
    "SybilAttack",
    # Human-in-the-Loop
    "ApprovalFatigueTrap",
    "SocialEngineeringTrap",
]
