"""
Run the deterministic benchmark suite and save results to disk.

Usage
-----
    python scripts/run_benchmark.py [options]
    # or, after pip install:
    ait-benchmark [options]

Options
-------
    --output-dir DIR    Directory for result JSON files (default: results/)
    --seed INT          Random seed for reproducibility (default: 42)
    --model MODEL       LLM model name for LLM-as-judge metric (default: keyword)
    --budget FLOAT      Maximum USD budget for LLM calls (default: no limit)

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_agent_traps.benchmark import BenchmarkEntry
    from ai_agent_traps.metrics.base import SuccessMetric


def _build_metric(model: str | None, budget: float | None) -> SuccessMetric:

    if model is None:
        from ai_agent_traps.metrics.keyword_overlap import KeywordOverlapMetric
        return KeywordOverlapMetric()

    try:
        from ai_agent_traps.metrics.llm_judge import LLMJudgeMetric
    except ImportError:
        print(
            "LLM metric requires [llm] extra: pip install -e '.[llm]'",
            file=sys.stderr,
        )
        sys.exit(1)

    return LLMJudgeMetric(model=model, budget_usd=budget)


_AGENT_REGISTRY: dict[str, str] = {
    "naive": "NaiveAgent",
    "filtered": "FilteredAgent",
    "memory": "MemoryAgent",
    "echo": "EchoAgent",
}

# LLM agents: (module_path, class_name, default_model)
_LLM_AGENTS: dict[str, tuple[str, str, str]] = {
    "anthropic": (
        "ai_agent_traps.agents.anthropic_agent",
        "AnthropicAgent",
        "claude-haiku-4-5-20251001",
    ),
    "openai": (
        "ai_agent_traps.agents.openai_agent",
        "OpenAIAgent",
        "gpt-4o-mini",
    ),
}


def _build_entries(
    agent_name: str = "naive",
    budget: float | None = None,
) -> tuple[list[BenchmarkEntry], object | None]:
    """Create one BenchmarkEntry per trap subtype.

    Returns (entries, llm_agent_instance_or_None). The llm_agent instance
    is returned so callers can inspect total_cost_usd after the run.
    """
    import importlib

    from ai_agent_traps.benchmark import BenchmarkEntry  # noqa: F811

    llm_agent_instance = None
    key = agent_name.lower()

    if key in _LLM_AGENTS:
        mod_path, cls_name, default_model = _LLM_AGENTS[key]
        try:
            mod = importlib.import_module(mod_path)
        except ImportError as exc:
            print(
                f"LLM agent requires [llm] extra: pip install -e '.[llm]'\n{exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        agent_cls = getattr(mod, cls_name)
        llm_agent_instance = agent_cls(model=default_model, budget_usd=budget)
        agent_factory = lambda: llm_agent_instance  # noqa: E731  shared instance
        agent_label = f"{cls_name}({default_model})"
    else:
        import ai_agent_traps.agent as _agent_mod

        agent_cls_name = _AGENT_REGISTRY.get(key)
        if agent_cls_name is None:
            valid = ", ".join({**_AGENT_REGISTRY, **_LLM_AGENTS})
            raise ValueError(f"Unknown agent {agent_name!r}. Valid options: {valid}")
        agent_cls = getattr(_agent_mod, agent_cls_name)
        agent_factory = agent_cls
        agent_label = agent_cls_name

    from ai_agent_traps.agent import NaiveAgent  # noqa: F401 (kept for compat)
    from ai_agent_traps.benchmark import BenchmarkEntry
    from ai_agent_traps.config import DEFAULT_CONFIG
    from ai_agent_traps.metrics.keyword_overlap import KeywordOverlapMetric
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
    from ai_agent_traps.traps.hitl import ApprovalFatigueTrap, SocialEngineeringTrap
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

    instruction = DEFAULT_CONFIG.simulation.default_instruction
    metric = KeywordOverlapMetric()

    trap_classes = [
        # Content Injection
        WebStandardObfuscation,
        DynamicCloaking,
        SteganographicPayload,
        SyntacticMasking,
        # Semantic Manipulation
        BiasedPhrasing,
        OversightCriticEvasion,
        PersonaHyperstition,
        # Cognitive State
        RAGKnowledgePoisoning,
        LatentMemoryPoisoning,
        ContextualLearningTrap,
        # Behavioural Control
        EmbeddedJailbreak,
        DataExfiltrationTrap,
        SubAgentSpawningTrap,
        # Systemic
        CongestionTrap,
        InterdependenceCascade,
        TacitCollusion,
        CompositionalFragment,
        SybilAttack,
        # Human-in-the-Loop
        ApprovalFatigueTrap,
        SocialEngineeringTrap,
    ]

    entries = []
    for cls in trap_classes:
        trap = cls()
        entries.append(
            BenchmarkEntry(
                trap=trap,
                agent_factory=agent_factory,
                metric=metric,
                hidden_instruction=instruction,
                description=f"{trap.spec.subtype.value} / {agent_label}",
            )
        )
    return entries, llm_agent_instance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AI Agent Traps deterministic benchmark suite."
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        metavar="DIR",
        help="Directory for result JSON files (default: results/)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="MODEL",
        help="LLM model name for LLM-as-judge metric (default: keyword overlap)",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=None,
        metavar="USD",
        help="Maximum USD budget for LLM calls",
    )
    parser.add_argument(
        "--agent",
        default="naive",
        metavar="AGENT",
        help=(
            f"Agent to evaluate against. "
            f"Mock: {', '.join(_AGENT_REGISTRY)}. "
            f"LLM: {', '.join(_LLM_AGENTS)}. (default: naive)"
        ),
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("AI Agent Traps — Benchmark Runner")
    print("=" * 50)
    print(f"Agent:      {args.agent}")
    print(f"Seed:       {args.seed}")
    print(f"Metric:     {args.model or 'keyword-overlap'}")
    print(f"Budget:     {'unlimited' if args.budget is None else f'${args.budget:.2f}'}")
    print(f"Output dir: {output_dir}")
    print()

    try:
        from ai_agent_traps.benchmark import BenchmarkSuite
    except ImportError as exc:
        print(f"Import error: {exc}", file=sys.stderr)
        print("Install with: pip install -e '.[dev]'", file=sys.stderr)
        return 1

    suite = BenchmarkSuite(name="full-sweep", seed=args.seed)
    entries, llm_agent = _build_entries(args.agent, budget=args.budget)
    for entry in entries:
        suite.add(entry)

    print(f"Running {len(suite.entries)} benchmark entries...")
    t0 = time.perf_counter()
    results = suite.run()
    elapsed = time.perf_counter() - t0

    n_passed = sum(r.succeeded for r in results)
    print(f"Done in {elapsed:.1f}s — {n_passed}/{len(results)} succeeded")
    if llm_agent is not None and hasattr(llm_agent, "total_cost_usd"):
        print(f"LLM cost:   ${llm_agent.total_cost_usd:.4f} USD")
    print()

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = output_dir / f"benchmark_{timestamp}_{args.agent}_seed{args.seed}.json"
    suite.save(out_path, results=results)
    print(f"Results saved to: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
