"""
Quick smoke test — no API keys required.

Runs one trap per category against the mock NaiveAgent to verify the
installation is correct. Exits with code 0 on success, 1 on failure.

Usage
-----
    python scripts/quick_smoke_test.py
    # or, after pip install:
    ait-smoke-test

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438
"""

from __future__ import annotations

import sys
import traceback


def main() -> int:
    print("AI Agent Traps — Quick Smoke Test")
    print("=" * 50)

    try:
        from ai_agent_traps.agent import NaiveAgent
        from ai_agent_traps.evaluate import run_category_sweep
        from ai_agent_traps.traps.behavioural import EmbeddedJailbreak
        from ai_agent_traps.traps.cognitive_state import RAGKnowledgePoisoning
        from ai_agent_traps.traps.content_injection import WebStandardObfuscation
        from ai_agent_traps.traps.hitl import ApprovalFatigueTrap
        from ai_agent_traps.traps.semantic import BiasedPhrasing
        from ai_agent_traps.traps.systemic import CongestionTrap
    except ImportError as exc:
        print(f"FAIL — import error: {exc}")
        print("  Install with: pip install -e '.[dev]'")
        return 1

    # One trap per category (no LLM calls, no network, no API keys)
    traps = [
        WebStandardObfuscation(),       # Content Injection
        BiasedPhrasing(),               # Semantic Manipulation
        RAGKnowledgePoisoning(),        # Cognitive State
        EmbeddedJailbreak(),            # Behavioural Control
        CongestionTrap(),               # Systemic
        ApprovalFatigueTrap(),          # Human-in-the-Loop
    ]
    from ai_agent_traps.agent import AgentProtocol

    agents: list[AgentProtocol] = [NaiveAgent()]

    failures: list[str] = []
    for trap in traps:
        category = trap.spec.category.value
        subtype = trap.spec.subtype.value
        try:
            suite = run_category_sweep([trap], agents, n_trials=1)
            assert len(suite.results) == 1, "Expected exactly one result"
            result = suite.results[0]
            status = "PASS"
            detail = f"succeeded={result.succeeded}  latency={result.latency_ms:.1f}ms"
        except Exception:  # noqa: BLE001
            status = "FAIL"
            detail = traceback.format_exc().splitlines()[-1]
            failures.append(f"{category} / {subtype}")

        label = f"  {category[:30]:<30} {subtype[:30]:<30}"
        print(f"{label}  [{status}]  {detail}")

    print("=" * 50)
    if failures:
        print(f"FAILED ({len(failures)}/{len(traps)}):")
        for name in failures:
            print(f"  - {name}")
        return 1

    print(f"All {len(traps)} smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
