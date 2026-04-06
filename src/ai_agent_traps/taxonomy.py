"""
AI Agent Traps — Taxonomy Encoding

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Implements: Complete encoding of Table 1 (p. 4) — the six-category taxonomy of
adversarial attacks targeting AI agents navigating the web.

Section references:
  §Abstract — six category names and one-line descriptions
  §Framework of Agent Traps (p. 3) — categorisation principle
  Table 1 (p. 4) — complete taxonomy with targets and mechanisms
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# §Framework of Agent Traps (p. 3)
# "We propose a framework categorising agent traps based on the component of
#  the agent's functional architecture they target."
# ---------------------------------------------------------------------------

class TrapTarget(Enum):
    """Table 1 — The six functional components of an agent that traps target."""
    PERCEPTION = "Perception"           # Content Injection Traps
    REASONING = "Reasoning"             # Semantic Manipulation Traps
    MEMORY_AND_LEARNING = "Memory & Learning"  # Cognitive State Traps
    ACTION = "Action"                   # Behavioural Control Traps
    MULTI_AGENT_DYNAMICS = "Multi-Agent Dynamics"  # Systemic Traps
    HUMAN_OVERSEER = "Human Overseer"   # Human-in-the-Loop Traps


class TrapCategory(Enum):
    """Table 1 — The six top-level trap categories.

    §Abstract: "six types of attack: Content Injection Traps...Semantic
    Manipulation Traps...Cognitive State Traps...Behavioural Control Traps...
    Systemic Traps...and Human-in-the-Loop Traps."
    """
    CONTENT_INJECTION = "Content Injection Traps"
    SEMANTIC_MANIPULATION = "Semantic Manipulation Traps"
    COGNITIVE_STATE = "Cognitive State Traps"
    BEHAVIOURAL_CONTROL = "Behavioural Control Traps"
    SYSTEMIC = "Systemic Traps"
    HUMAN_IN_THE_LOOP = "Human-in-the-Loop Traps"


class TrapSubtype(Enum):
    """Table 1 — All 17 named subtypes across the six categories."""

    # --- Content Injection Traps ---
    WEB_STANDARD_OBFUSCATION = "Web-Standard Obfuscation"
    DYNAMIC_CLOAKING = "Dynamic Cloaking"
    STEGANOGRAPHIC_PAYLOADS = "Steganographic Payloads"
    SYNTACTIC_MASKING = "Syntactic Masking"

    # --- Semantic Manipulation Traps ---
    BIASED_PHRASING = "Biased Phrasing, Framing & Contextual Priming"
    OVERSIGHT_CRITIC_EVASION = "Oversight & Critic Evasion"
    PERSONA_HYPERSTITION = "Persona Hyperstition"

    # --- Cognitive State Traps ---
    RAG_KNOWLEDGE_POISONING = "RAG Knowledge Poisoning"
    LATENT_MEMORY_POISONING = "Latent Memory Poisoning"
    CONTEXTUAL_LEARNING_TRAPS = "Contextual Learning Traps"

    # --- Behavioural Control Traps ---
    EMBEDDED_JAILBREAK = "Embedded Jailbreak Sequences"
    DATA_EXFILTRATION = "Data Exfiltration Traps"
    SUB_AGENT_SPAWNING = "Sub-agent Spawning Traps"

    # --- Systemic Traps ---
    CONGESTION = "Congestion Traps"
    INTERDEPENDENCE_CASCADE = "Interdependence Cascades"
    TACIT_COLLUSION = "Tacit Collusion"
    COMPOSITIONAL_FRAGMENT = "Compositional Fragment Traps"
    SYBIL_ATTACK = "Sybil Attacks"

    # --- Human-in-the-Loop Traps ---
    # [PARTIALLY_SPECIFIED] The paper does not enumerate named subtypes for
    # this category, describing it as an emerging / largely unexplored surface.
    # "systematically targeting the human overseer via a compromised agent
    # remains a largely unexplored attack surface" (§Human-in-the-Loop, p. 15)
    APPROVAL_FATIGUE = "Approval Fatigue"          # [PARTIALLY_SPECIFIED] §p.15
    SOCIAL_ENGINEERING = "Social Engineering"       # [PARTIALLY_SPECIFIED] §p.15


class MaturityLevel(Enum):
    """
    [UNSPECIFIED] The paper implicitly distinguishes trap types by empirical
    evidence. This enum encodes that distinction from the prose.

    Using: three-level scale inferred from language in each section.
    Alternatives: binary (empirical / theoretical), continuous score.

    Evidence:
    - "better-understood threats" for Content Injection and Behavioural Control
      (§Framework, p. 3)
    - "more theoretical attack surface anticipated to emerge" for Systemic and
      Human-in-the-Loop (§Framework, p. 3)
    """
    EMPIRICAL = "empirical"      # Demonstrated in published research
    PARTIAL = "partial"          # Some evidence exists
    THEORETICAL = "theoretical"  # Hypothetical / emerging


# ---------------------------------------------------------------------------
# Table 1 (p. 4) — Structured representation of each trap type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrapSpec:
    """Structured encoding of one row in Table 1 (p. 4).

    Every field either quotes the paper directly or is flagged.
    """
    subtype: TrapSubtype
    category: TrapCategory
    target: TrapTarget

    # Table 1, column 2: the one-sentence mechanism description from the table
    table_description: str

    # The agent capability being exploited (from prose, not table)
    # [PARTIALLY_SPECIFIED] Not in table; inferred from prose descriptions.
    exploited_capability: str

    # Maturity level — [UNSPECIFIED] inferred from paper language
    maturity: MaturityLevel = MaturityLevel.EMPIRICAL

    # Selected success-rate references from cited papers (not paper's own data)
    # [PARTIALLY_SPECIFIED] These come from cited third-party papers, not from
    # novel experiments by the authors.
    empirical_success_refs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Complete taxonomy — encoding Table 1 row by row
# ---------------------------------------------------------------------------

# Table 1 (p. 4): "Exploiting the divergence between machine-parsed content
# and human-visible rendering to embed hidden commands."
CONTENT_INJECTION_MECHANISM = (
    "Exploiting the divergence between machine-parsed content and "
    "human-visible rendering to embed hidden commands."
)

# Table 1 (p. 4): "Manipulating input data distributions to corrupt reasoning
# without issuing overt commands."
SEMANTIC_MANIPULATION_MECHANISM = (
    "Manipulating input data distributions to corrupt reasoning "
    "without issuing overt commands."
)

# Table 1 (p. 4): "Corrupting an agent's long-term memory, knowledge bases,
# and its learned behavioural policies."
COGNITIVE_STATE_MECHANISM = (
    "Corrupting an agent's long-term memory, knowledge bases, "
    "and its learned behavioural policies."
)

# Table 1 (p. 4): "Explicit commands that target instruction-following
# capabilities to serve attacker goals."
BEHAVIOURAL_CONTROL_MECHANISM = (
    "Explicit commands that target instruction-following "
    "capabilities to serve attacker goals."
)

# Table 1 (p. 4): "Seeding the environment with inputs designed to trigger
# macro-level failures via correlated agent behaviour."
SYSTEMIC_MECHANISM = (
    "Seeding the environment with inputs designed to trigger "
    "macro-level failures via correlated agent behaviour."
)

# Table 1 (p. 4): "Commandeering the agent to attack the human overseer by
# exploiting cognitive biases."
HITL_MECHANISM = (
    "Commandeering the agent to attack the human overseer by "
    "exploiting cognitive biases."
)


TAXONOMY: list[TrapSpec] = [

    # -----------------------------------------------------------------------
    # Content Injection Traps (Table 1, p. 4; §Content Injection, pp. 4-6)
    # -----------------------------------------------------------------------
    TrapSpec(
        subtype=TrapSubtype.WEB_STANDARD_OBFUSCATION,
        category=TrapCategory.CONTENT_INJECTION,
        target=TrapTarget.PERCEPTION,
        table_description=(
            "Embeds commands via CSS, HTML comments, or metadata attributes "
            "invisible to humans but parsed by agents."
        ),
        exploited_capability="HTML/CSS/metadata ingestion pipeline",
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Verma & Yadav 2025 — 15-29% alteration of generated summaries",
            "Evtimov et al. 2025 (WASP) — up to 86% partial commandeering",
            "Johnson et al. 2025 — reliably hijack agent behaviour via accessibility tree",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.DYNAMIC_CLOAKING,
        category=TrapCategory.CONTENT_INJECTION,
        target=TrapTarget.PERCEPTION,
        table_description=(
            "Detects agent visitors and conditionally injects payloads "
            "absent for human users."
        ),
        exploited_capability=(
            "Differential content serving; browser fingerprinting / "
            "automation-framework detection"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Zychlinski 2025 — describes parallel-poisoned web visible only to AI agents",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.STEGANOGRAPHIC_PAYLOADS,
        category=TrapCategory.CONTENT_INJECTION,
        target=TrapTarget.PERCEPTION,
        table_description=(
            "Encodes adversarial instructions in media file binary data "
            "(e.g., pixel arrays) imperceptible to humans."
        ),
        exploited_capability="Multimodal pixel/audio array parsing",
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Cheddad et al. 2010 — LSB steganography baseline",
            "Bagdasaryan et al. 2023 — abusing images/sounds for indirect injection",
            "Pathade 2025 — invisible injections via steganographic prompt embedding",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.SYNTACTIC_MASKING,
        category=TrapCategory.CONTENT_INJECTION,
        target=TrapTarget.PERCEPTION,
        table_description=(
            "Leverages formatting language syntax (e.g., Markdown, LaTeX) "
            "to cloak payloads targeting the agent's parsing layer."
        ),
        exploited_capability="Formatting-language rendering pipeline",
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Keuper 2025 — white-on-white / tiny-font LaTeX in scientific manuscripts",
            "Xiong et al. 2025 — malicious font files alter code-to-glyph mappings",
        ],
    ),

    # -----------------------------------------------------------------------
    # Semantic Manipulation Traps (Table 1, p. 4; §Semantic, pp. 7-8)
    # -----------------------------------------------------------------------
    TrapSpec(
        subtype=TrapSubtype.BIASED_PHRASING,
        category=TrapCategory.SEMANTIC_MANIPULATION,
        target=TrapTarget.REASONING,
        table_description=(
            "Saturates source content with sentiment-laden or authoritative "
            "language to statistically bias the agent's synthesis."
        ),
        exploited_capability=(
            "Framing Effect susceptibility; contextual bias in LLM synthesis "
            "(Tversky & Kahneman, 1981)"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Sumita et al. 2025 — cognitive biases alter model outputs",
            "Ben-Zion et al. 2025 — inducing state anxiety reproduces human-like biases",
            "Bisconti et al. 2025 — adversarial poetry amplifies jailbreak success",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.OVERSIGHT_CRITIC_EVASION,
        category=TrapCategory.SEMANTIC_MANIPULATION,
        target=TrapTarget.REASONING,
        table_description=(
            "Wraps malicious instructions in educational, hypothetical, or "
            "red-teaming framing to bypass safety filters and oversight mechanisms."
        ),
        exploited_capability=(
            "Internal critic / constitutional verifier heuristics; "
            "jailbreak via instruction misdirection and simulation-based bypass"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Shen et al. 2024 — 'do anything now' jailbreak characterisation",
            "Weinberg 2025 — instruction misdirection and simulation-based bypass",
            "Kirch et al. 2025 — nonlinear latent features drive jailbreak success",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.PERSONA_HYPERSTITION,
        category=TrapCategory.SEMANTIC_MANIPULATION,
        target=TrapTarget.REASONING,
        table_description=(
            "Seeds a narrative about a model's identity that re-enters via "
            "retrieval, producing outputs that reinforce the label."
        ),
        exploited_capability=(
            "Retrieval-augmented context re-ingestion; training-data feedback "
            "loop via circulating narratives (Shanahan & Singler, 2024)"
        ),
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Shanahan & Singler 2024 — esoteric AI narratives surface in conversations",
            "Anthropic 2025 / Bowman & Fish 2025 — 'spiritual bliss attractor'",
        ],
    ),

    # -----------------------------------------------------------------------
    # Cognitive State Traps (Table 1, p. 4; §Cognitive State, pp. 9-10)
    # -----------------------------------------------------------------------
    TrapSpec(
        subtype=TrapSubtype.RAG_KNOWLEDGE_POISONING,
        category=TrapCategory.COGNITIVE_STATE,
        target=TrapTarget.MEMORY_AND_LEARNING,
        table_description=(
            "Injects fabricated statements into retrieval corpora so agents "
            "treat attacker content as verified fact."
        ),
        exploited_capability="Retrieval-augmented generation (RAG) ingestion pipeline",
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Zou et al. 2025 — handful of optimised docs reliably manipulates outputs",
            "Xue et al. 2024 (Badrag) — retrieval backdoors surface attacker content",
            "Clop & Teglia 2024 — backdoored retrievers for prompt injection",
            "Zhang et al. 2025b (PoisonedEye) — multimodal RAG poisoning",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.LATENT_MEMORY_POISONING,
        category=TrapCategory.COGNITIVE_STATE,
        target=TrapTarget.MEMORY_AND_LEARNING,
        table_description=(
            "Implants innocuous data into internal memory stores that activates "
            "as malicious when retrieved in a specific future context."
        ),
        exploited_capability=(
            "Episodic memory write-retrieve loop; persistent memory across sessions "
            "(Kang et al., 2025; Zhang et al., 2025d)"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Dong et al. 2025 — >80% success with <0.1% data poisoning",
            "Chen et al. 2024 (AgentPoison) — backdoor trigger mapped to embedding subspace",
            "Wang et al. 2025a — memory extraction via purpose-built extraction prompts",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.CONTEXTUAL_LEARNING_TRAPS,
        category=TrapCategory.COGNITIVE_STATE,
        target=TrapTarget.MEMORY_AND_LEARNING,
        table_description=(
            "Corrupts few-shot demonstrations or reward signals to steer "
            "in-context learning toward attacker-defined objectives."
        ),
        exploited_capability=(
            "In-context few-shot learning; online RL reward signals; "
            "demonstration-poisoning (Wang et al., 2023)"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Zhao et al. 2024 — 95% success rate via poisoned demonstrations",
            "He et al. 2025 — discrete text perturbations to demonstration examples",
            "Sasnauskas et al. 2025 — test-time reward poisoning degrades RL returns",
            "Yang et al. 2025 — human feedback attacks on online RLHF",
        ],
    ),

    # -----------------------------------------------------------------------
    # Behavioural Control Traps (Table 1, p. 4; §Behavioural, pp. 10-11)
    # -----------------------------------------------------------------------
    TrapSpec(
        subtype=TrapSubtype.EMBEDDED_JAILBREAK,
        category=TrapCategory.BEHAVIOURAL_CONTROL,
        target=TrapTarget.ACTION,
        table_description=(
            "Dormant adversarial prompts embedded in external resources that "
            "override safety alignment upon ingestion."
        ),
        exploited_capability=(
            "Indirect prompt injection via external resource ingestion; "
            "safety-alignment overriding (Greshake et al., 2023)"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Evtimov et al. 2025 (WASP) — web agents frequently execute injected instructions",
            "Chen et al. 2025c — adversarial pop-ups hijack vision-language computer agents",
            "Qi et al. 2024 — single image jailbreaks vision-language models universally",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.DATA_EXFILTRATION,
        category=TrapCategory.BEHAVIOURAL_CONTROL,
        target=TrapTarget.ACTION,
        table_description=(
            "Induces the agent to locate, encode, and exfiltrate private or "
            "sensitive data to attacker-controlled endpoints."
        ),
        exploited_capability=(
            "Confused deputy vulnerability (Hardy, 1988); tool-calling with "
            "network access; privileged context read + write"
        ),
        maturity=MaturityLevel.EMPIRICAL,
        empirical_success_refs=[
            "Shapira et al. 2025 — >80% success across five agents",
            "Reddy & Gujral 2025 (EchoLeak) — M365 Copilot exfiltrates entire context",
            "Cohen et al. 2024 — zero-click worms via self-replicating prompts",
            "Alizadeh et al. 2025 — banking-style scenarios in AgentDojo",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.SUB_AGENT_SPAWNING,
        category=TrapCategory.BEHAVIOURAL_CONTROL,
        target=TrapTarget.ACTION,
        table_description=(
            "Exploits orchestrator privileges to instantiate attacker-controlled "
            "sub-agents within the trusted control flow."
        ),
        exploited_capability=(
            "Orchestrator ability to spawn sub-agents and delegate tasks "
            "(Tomašev et al., 2026)"
        ),
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Triedman et al. 2025 — 58-90% success hijacking multi-agent control flow",
        ],
    ),

    # -----------------------------------------------------------------------
    # Systemic Traps (Table 1, p. 4; §Systemic, pp. 12-14)
    # -----------------------------------------------------------------------
    TrapSpec(
        subtype=TrapSubtype.CONGESTION,
        category=TrapCategory.SYSTEMIC,
        target=TrapTarget.MULTI_AGENT_DYNAMICS,
        table_description=(
            "Broadcasts signals that synchronise homogeneous agents into "
            "exhaustive demand for limited resources."
        ),
        exploited_capability=(
            "Homogeneous reward function / shared environmental signal; "
            "congestion game dynamics (Rosenthal, 1973)"
        ),
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Gleave et al. 2019 — adversarial policies attack deep RL",
            "Blumenkamp & Prorok 2021 — adversarial communication in MARL",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.INTERDEPENDENCE_CASCADE,
        category=TrapCategory.SYSTEMIC,
        target=TrapTarget.MULTI_AGENT_DYNAMICS,
        table_description=(
            "Perturbs a fragile equilibrium to trigger rapid, self-amplifying "
            "cascades across interdependent agents."
        ),
        exploited_capability=(
            "Reactive feedback loops across sequentially interdependent agents; "
            "financial network fragility (Acemoglu et al., 2015)"
        ),
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Gu et al. 2024 — infectious jailbreak spreads exponentially via pairwise interactions",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.TACIT_COLLUSION,
        category=TrapCategory.SYSTEMIC,
        target=TrapTarget.MULTI_AGENT_DYNAMICS,
        table_description=(
            "Embeds environmental signals as correlation devices to synchronise "
            "anti-competitive behaviour without direct inter-agent communication."
        ),
        exploited_capability=(
            "Correlated equilibrium via shared environmental observables "
            "(Aumann, 1974/1987; Calvano et al., 2020)"
        ),
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Calvano et al. 2020 — AI agents coordinate supra-competitive prices",
            "Klein 2021 — Q-learning under sequential pricing learns collusion",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.COMPOSITIONAL_FRAGMENT,
        category=TrapCategory.SYSTEMIC,
        target=TrapTarget.MULTI_AGENT_DYNAMICS,
        table_description=(
            "Partitions a payload into semantically benign fragments that "
            "reconstitute into a full trigger upon multi-agent aggregation."
        ),
        exploited_capability=(
            "Multi-agent information aggregation; distributed confused deputy; "
            "composite backdoor (Huang et al., 2024)"
        ),
        maturity=MaturityLevel.THEORETICAL,
        empirical_success_refs=[
            "Huang et al. 2024 — composite backdoor attacks in LLMs",
            "Tong et al. 2024 — distributed backdoor triggers",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.SYBIL_ATTACK,
        category=TrapCategory.SYSTEMIC,
        target=TrapTarget.MULTI_AGENT_DYNAMICS,
        table_description=(
            "Fabricates multiple pseudonymous agent identities to "
            "disproportionately influence collective decision-making."
        ),
        exploited_capability=(
            "Trust assumptions and reputation mechanisms in multi-agent systems; "
            "LLM conformity tendencies (Cui & Du, 2025)"
        ),
        maturity=MaturityLevel.PARTIAL,
        empirical_success_refs=[
            "Leibo et al. 2025 — coherent identity assumptions undermined by counterfeit entities",
            "Cui & Du 2025 (MAD-SPEAR) — conformity-driven attack on multi-agent debate",
        ],
    ),

    # -----------------------------------------------------------------------
    # Human-in-the-Loop Traps (Table 1, p. 4; §HITL, p. 15)
    # NOTE: The paper identifies this as an emerging, largely unexplored surface.
    # "systematically targeting the human overseer via a compromised agent
    # remains a largely unexplored attack surface that warrants further research."
    # -----------------------------------------------------------------------
    TrapSpec(
        subtype=TrapSubtype.APPROVAL_FATIGUE,
        category=TrapCategory.HUMAN_IN_THE_LOOP,
        target=TrapTarget.HUMAN_OVERSEER,
        table_description=(
            "Generates outputs calibrated to induce 'approval fatigue' in human "
            "reviewers, exploiting cognitive fatigue⁴ and automation bias⁵."
        ),
        exploited_capability=(
            "Automation bias (Goddard et al., 2012)⁵; cognitive fatigue⁴; "
            "non-expert summarisation trust"
        ),
        maturity=MaturityLevel.THEORETICAL,
        empirical_success_refs=[
            "OECD AI Policy Observatory 2025 — ransomware step-by-step via CSS obfuscation",
        ],
    ),
    TrapSpec(
        subtype=TrapSubtype.SOCIAL_ENGINEERING,
        category=TrapCategory.HUMAN_IN_THE_LOOP,
        target=TrapTarget.HUMAN_OVERSEER,
        table_description=(
            "Induces the human-in-the-loop to click malicious hyperlinks or "
            "authorise harmful actions via social engineering."
        ),
        exploited_capability=(
            "Human cognitive biases; social engineering via agent-generated content"
        ),
        maturity=MaturityLevel.THEORETICAL,
        empirical_success_refs=[
            "Deng et al. 2025 — prompt injections used to insert phishing links",
        ],
    ),
]


def get_by_category(category: TrapCategory) -> list[TrapSpec]:
    """Return all TrapSpecs for a given category."""
    return [t for t in TAXONOMY if t.category == category]


def get_by_target(target: TrapTarget) -> list[TrapSpec]:
    """Return all TrapSpecs targeting a given agent component."""
    return [t for t in TAXONOMY if t.target == target]


def get_by_maturity(maturity: MaturityLevel) -> list[TrapSpec]:
    """Return all TrapSpecs at a given empirical maturity level."""
    return [t for t in TAXONOMY if t.maturity == maturity]


def get_spec(subtype: TrapSubtype) -> TrapSpec:
    """Return the TrapSpec for a specific subtype.

    Raises
    ------
    ValueError
        If *subtype* is not found in TAXONOMY (should never happen for valid
        ``TrapSubtype`` enum members since every member has a corresponding entry).
    """
    for t in TAXONOMY:
        if t.subtype == subtype:
            return t
    raise ValueError(f"No TrapSpec found for subtype {subtype!r}")
