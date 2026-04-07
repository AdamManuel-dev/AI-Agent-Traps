"""
Generate a LaTeX comparison table of simulated results vs. paper-cited rates.

Usage
-----
    python scripts/generate_paper_table.py [options]
    # or, after pip install:
    ait-paper-table [options]

Options
-------
    --output FILE   Write LaTeX table to this file (default: stdout)
    --agents NAMES  Comma-separated agent types: naive,filtered,echo,memory
                    (default: naive,filtered)
    --n-trials INT  Trials per (trap, agent) pair (default: 3)

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438
"""

from __future__ import annotations

import argparse
import sys


def _make_latex_table(
    sim_rates: dict[str, float],
    paper_refs: dict[str, dict[str, str]],
) -> str:
    """Render a LaTeX longtable comparing simulated vs. paper-cited rates."""
    from ai_agent_traps.taxonomy import TAXONOMY

    header = r"""\begin{longtable}{llrrp{5cm}}
\toprule
\textbf{Category} & \textbf{Trap Subtype} &
\textbf{Sim. Rate} & \textbf{Paper Rate} & \textbf{Paper Source} \\
\midrule
\endhead
\midrule
\multicolumn{5}{r}{\textit{Continued on next page}} \\
\endfoot
\bottomrule
\caption{Simulated vs. paper-cited success rates for AI Agent Traps
         (Franklin et al., 2025)}
\label{tab:trap-comparison}
\endlastfoot
"""
    footer = r"\end{longtable}"

    rows: list[str] = []
    last_category = ""
    for spec in TAXONOMY:
        subtype_val = spec.subtype.value
        category_val = spec.category.value

        # Category label only in first row of each group
        cat_tex = category_val if category_val != last_category else ""
        last_category = category_val

        sim_pct = sim_rates.get(subtype_val)
        sim_str = f"{sim_pct:.0%}" if sim_pct is not None else "—"

        ref = paper_refs.get(subtype_val)
        if ref:
            paper_rate = ref.get("rate", "—")
            paper_src = ref.get("source", "—")
        else:
            paper_rate = "—"
            paper_src = "not cited"

        # Escape % for LaTeX
        paper_rate_tex = paper_rate.replace("%", r"\%")
        sim_str_tex = sim_str.replace("%", r"\%")

        rows.append(
            f"  {cat_tex} & {subtype_val} & "
            f"{sim_str_tex} & {paper_rate_tex} & \\small {{{paper_src}}} \\\\"
        )

    return header + "\n".join(rows) + "\n" + footer


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate LaTeX comparison table (simulated vs. paper-cited rates)."
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write LaTeX to this file (default: stdout)",
    )
    parser.add_argument(
        "--agents",
        default="naive,filtered",
        metavar="NAMES",
        help="Comma-separated agent types: naive,filtered,echo,memory",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=3,
        metavar="N",
        help="Trials per (trap, agent) pair (default: 3)",
    )
    args = parser.parse_args()

    try:
        from ai_agent_traps.agent import EchoAgent, FilteredAgent, MemoryAgent, NaiveAgent
        from ai_agent_traps.evaluate import compute_paper_benchmarks, run_category_sweep
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
    except ImportError as exc:
        print(f"Import error: {exc}", file=sys.stderr)
        print("Install with: pip install -e '.[dev]'", file=sys.stderr)
        return 1

    agent_map = {
        "naive": NaiveAgent,
        "filtered": FilteredAgent,
        "echo": EchoAgent,
        "memory": MemoryAgent,
    }
    agents = []
    for name in args.agents.split(","):
        key = name.strip().lower()
        if key not in agent_map:
            print(f"Unknown agent '{key}'. Choose from: {list(agent_map)}", file=sys.stderr)
            return 1
        agents.append(agent_map[key]())

    traps = [
        WebStandardObfuscation(), DynamicCloaking(), SteganographicPayload(), SyntacticMasking(),
        BiasedPhrasing(), OversightCriticEvasion(), PersonaHyperstition(),
        RAGKnowledgePoisoning(), LatentMemoryPoisoning(), ContextualLearningTrap(),
        EmbeddedJailbreak(), DataExfiltrationTrap(), SubAgentSpawningTrap(),
        CongestionTrap(), InterdependenceCascade(), TacitCollusion(),
        CompositionalFragment(), SybilAttack(),
        ApprovalFatigueTrap(), SocialEngineeringTrap(),
    ]

    print("Running evaluation sweep...", file=sys.stderr)
    suite = run_category_sweep(traps, agents, n_trials=args.n_trials)

    # Aggregate simulated success rates by subtype
    sim_rates_raw: dict[str, list[bool]] = {}
    for result in suite.results:
        key = result.trap_subtype.value
        sim_rates_raw.setdefault(key, []).append(result.succeeded)

    sim_rate_map = {k: sum(v) / len(v) for k, v in sim_rates_raw.items()}

    paper_data = compute_paper_benchmarks()
    paper_refs: dict[str, dict[str, str]] = {}
    for key, val in paper_data["by_subtype"].items():
        # Normalize keys that have parenthetical qualifiers
        base_key = key.split(" (")[0]
        paper_refs.setdefault(base_key, dict(val))

    table_tex = _make_latex_table(sim_rate_map, paper_refs)

    if args.output:
        out_path = args.output
        with open(out_path, "w") as f:
            f.write(table_tex)
        print(f"LaTeX table written to: {out_path}", file=sys.stderr)
    else:
        print(table_tex)

    return 0


if __name__ == "__main__":
    sys.exit(main())
