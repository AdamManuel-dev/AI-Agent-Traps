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


def _build_entries(agent_name: str = "naive") -> list[BenchmarkEntry]:
    """Create one BenchmarkEntry per trap subtype (all 19 subtypes)."""
    import ai_agent_traps.agent as _agent_mod

    agent_cls_name = _AGENT_REGISTRY.get(agent_name.lower())
    if agent_cls_name is None:
        valid = ", ".join(_AGENT_REGISTRY)
        raise ValueError(f"Unknown agent {agent_name!r}. Valid options: {valid}")
    agent_cls = getattr(_agent_mod, agent_cls_name)

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
                agent_factory=agent_cls,
                metric=metric,
                hidden_instruction=instruction,
                description=f"{trap.spec.subtype.value} / {agent_cls_name}",
            )
        )
    return entries


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
        help=f"Agent to evaluate against. Options: {', '.join(_AGENT_REGISTRY)} (default: naive)",
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
    for entry in _build_entries(args.agent):
        suite.add(entry)

    print(f"Running {len(suite.entries)} benchmark entries...")
    t0 = time.perf_counter()
    results = suite.run()
    elapsed = time.perf_counter() - t0

    n_passed = sum(r.succeeded for r in results)
    print(f"Done in {elapsed:.1f}s — {n_passed}/{len(results)} succeeded")
    print()

    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = output_dir / f"benchmark_{timestamp}_{args.agent}_seed{args.seed}.json"
    suite.save(out_path, results=results)
    print(f"Results saved to: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
