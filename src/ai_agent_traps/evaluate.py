"""
AI Agent Traps — Evaluation Utilities

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

Implements: Evaluation framework for measuring trap effectiveness and
agent robustness.

§Mitigation Strategies (p. 16):
  "many categories of agent traps identified in this paper currently lack
   standardised benchmarks. Without systematic evaluation, the robustness of
   deployed agents against these threats remains unknown. We call on the
   research community to develop comprehensive evaluation suites and automated
   red-teaming methodologies that can probe these vulnerabilities at scale."

This module provides the scaffold for such evaluation.

[UNSPECIFIED] The paper calls for but does not specify evaluation metrics,
benchmark formats, or evaluation protocols. All choices below are our design
decisions for this research scaffold.
"""

from __future__ import annotations

import csv
import io
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ai_agent_traps.agent import AgentProtocol
    from ai_agent_traps.defenses.base import Defense
    from ai_agent_traps.metrics.base import SuccessMetric

from ai_agent_traps.config import DEFAULT_CONFIG
from ai_agent_traps.taxonomy import (
    MaturityLevel,
    TrapCategory,
    TrapSubtype,
    get_spec,
)
from ai_agent_traps.traps.base import AgentTrapBase, MultiAgentTrapBase, TrapResult


@dataclass
class EvalResult:
    """
    Result of evaluating one trap against one agent.

    [UNSPECIFIED] Metric definitions. The paper cites success rates from
    third-party papers but does not define a unified metric.
    Using: binary success + response latency.
    """
    trap_subtype: TrapSubtype
    trap_category: TrapCategory
    agent_type: str
    succeeded: bool
    latency_ms: float
    agent_response: str
    notes: str = ""

    @property
    def success_str(self) -> str:
        return "✓ SUCCEEDED" if self.succeeded else "✗ FAILED"

    def to_dict(self) -> dict[str, object]:
        return {
            "trap_subtype": self.trap_subtype.value,
            "trap_category": self.trap_category.value,
            "agent_type": self.agent_type,
            "succeeded": self.succeeded,
            "latency_ms": self.latency_ms,
            "agent_response": self.agent_response,
            "notes": self.notes,
        }


@dataclass
class MultiAgentEvalResult(EvalResult):
    """Evaluation result for multi-agent trap scenarios."""

    population_size: int = 0
    n_affected: int = 0  # Agents where succeeded=True
    cascade_depth_reached: int = 0  # Currently unused; reserved for cascade trap analysis
    convergence_rate: float = 0.0  # n_affected / population_size; 0.0 if no population

    def to_dict(self) -> dict[str, object]:
        """Extend parent to_dict with multi-agent fields."""
        base = super().to_dict()
        base.update(
            {
                "population_size": self.population_size,
                "n_affected": self.n_affected,
                "cascade_depth_reached": self.cascade_depth_reached,
                "convergence_rate": self.convergence_rate,
            }
        )
        return base


@dataclass
class EvalSuite:
    """
    Collection of evaluation results across multiple (trap, agent) pairs.

    The paper (§Mitigation, p. 16) calls for "comprehensive evaluation suites."
    This class provides the aggregation layer for such a suite.
    """
    results: list[EvalResult] = field(default_factory=list)

    def add(self, result: EvalResult) -> None:
        self.results.append(result)

    def success_rate(
        self,
        category: TrapCategory | None = None,
        maturity: MaturityLevel | None = None,
    ) -> float:
        """
        Compute success rate (fraction of traps that succeeded).

        [UNSPECIFIED] How to aggregate across trap subtypes and agents.
        Using: simple mean over all matching results.
        """
        filtered = self.results
        if category is not None:
            filtered = [r for r in filtered if r.trap_category == category]
        if maturity is not None:
            filtered = [
                r for r in filtered
                if (spec := get_spec(r.trap_subtype)) and spec.maturity == maturity
            ]
        if not filtered:
            return 0.0
        return sum(r.succeeded for r in filtered) / len(filtered)

    def category_breakdown(self) -> dict[str, dict[str, Any]]:
        """Return success rate per category."""
        breakdown = {}
        for cat in TrapCategory:
            cat_results = [r for r in self.results if r.trap_category == cat]
            if not cat_results:
                continue
            rate = sum(r.succeeded for r in cat_results) / len(cat_results)
            breakdown[cat.value] = {
                "n_evaluated": len(cat_results),
                "n_succeeded": sum(r.succeeded for r in cat_results),
                "success_rate": rate,
            }
        return breakdown

    def summary(self) -> str:
        """Print a human-readable summary of evaluation results."""
        lines = [
            "=" * 60,
            "AI Agent Traps — Evaluation Summary",
            "Franklin et al. (2025), Table 1",
            "=" * 60,
            f"Total evaluations: {len(self.results)}",
            f"Overall success rate: {self.success_rate():.1%}",
            "",
            "By category:",
        ]
        for cat_name, stats in self.category_breakdown().items():
            lines.append(
                f"  {cat_name[:40]:<40} "
                f"{stats['success_rate']:.1%} "
                f"({stats['n_succeeded']}/{stats['n_evaluated']})"
            )
        lines.append("")
        lines.append(
            "[UNSPECIFIED] Success metric: keyword overlap between "
            "agent response and hidden instruction. "
            "See REPRODUCTION_NOTES.md §Unspecified choices."
        )
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        """Serialize the entire evaluation suite to a dictionary."""
        return {
            "total_evaluations": len(self.results),
            "overall_success_rate": self.success_rate(),
            "category_breakdown": self.category_breakdown(),
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self) -> str:
        """Return JSON Lines (one EvalResult per line)."""
        return "\n".join(json.dumps(r.to_dict()) for r in self.results)

    def to_csv(self) -> str:
        """Return CSV with header row.

        Derives fieldnames as the union across all result dicts so that
        heterogeneous types (EvalResult + MultiAgentEvalResult) serialize
        without crashing.  Missing fields emit empty strings.
        """
        if not self.results:
            return ""
        # Derive header as union of all result dicts to handle heterogeneous types
        all_keys: list[str] = []
        seen: set[str] = set()
        for r in self.results:
            for k in r.to_dict():
                if k not in seen:
                    all_keys.append(k)
                    seen.add(k)
        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=all_keys, extrasaction="ignore", restval=""
        )
        writer.writeheader()
        writer.writerows(r.to_dict() for r in self.results)
        return output.getvalue()

    def systemic_summary(self) -> dict[str, Any]:
        """Aggregate stats for MultiAgentEvalResult entries.

        Returns
        -------
        dict
            Keys: n_systemic_results, avg_convergence_rate,
            max_convergence_rate, avg_population_size, by_trap.
        """
        systemic = [r for r in self.results if isinstance(r, MultiAgentEvalResult)]
        if not systemic:
            return {
                "n_systemic_results": 0,
                "avg_convergence_rate": 0.0,
                "max_convergence_rate": 0.0,
                "avg_population_size": 0.0,
                "by_trap": {},
            }

        avg_conv = sum(r.convergence_rate for r in systemic) / len(systemic)
        max_conv = max(r.convergence_rate for r in systemic)
        avg_pop = sum(r.population_size for r in systemic) / len(systemic)

        by_trap: dict[str, dict[str, list[float]]] = {}
        for result in systemic:
            key = result.trap_subtype.value
            if key not in by_trap:
                by_trap[key] = {"rates": [], "populations": []}
            by_trap[key]["rates"].append(result.convergence_rate)
            by_trap[key]["populations"].append(float(result.population_size))

        by_trap_summary: dict[str, dict[str, float | int]] = {}
        for key, data in by_trap.items():
            rates = data["rates"]
            by_trap_summary[key] = {
                "avg_convergence_rate": sum(rates) / len(rates),
                "max_convergence_rate": max(rates),
                "n_results": len(rates),
            }

        return {
            "n_systemic_results": len(systemic),
            "avg_convergence_rate": avg_conv,
            "max_convergence_rate": max_conv,
            "avg_population_size": avg_pop,
            "by_trap": by_trap_summary,
        }

    def save(self, path: str | Path, format: str = "json") -> None:
        """Write to file in json or csv format."""
        p = Path(path)
        if format == "json":
            p.write_text(self.to_json())
        elif format == "csv":
            p.write_text(self.to_csv())
        else:
            raise ValueError(f"Unsupported format: {format!r}. Use 'json' or 'csv'.")


def run_single_eval(
    trap: AgentTrapBase,
    agent: AgentProtocol,
    hidden_instruction: str,
    target_context: str | None = None,
    metric: SuccessMetric | None = None,
) -> EvalResult:
    """
    Run a single trap against a single agent and record the result.

    Parameters
    ----------
    trap : AgentTrapBase
        Trap instance to evaluate.
    agent : AgentProtocol
        Target agent.
    hidden_instruction : str
        Instruction embedded in the payload.
    target_context : str, optional
        Context about the target environment.
    metric : SuccessMetric, optional
        Pluggable success metric. When provided, overrides the trap's built-in
        ``_check_succeeded`` result with ``metric.judge()``.

    [UNSPECIFIED] Timing methodology. Using: wall-clock time of process() call.
    """
    t0 = time.perf_counter()
    result: TrapResult = trap.evaluate(
        hidden_instruction, agent, target_context
    )
    t1 = time.perf_counter()

    succeeded = result.succeeded
    if metric is not None:
        succeeded = metric.judge(
            result.agent_response, hidden_instruction, result.payload
        )

    return EvalResult(
        trap_subtype=trap.spec.subtype,
        trap_category=trap.spec.category,
        agent_type=type(agent).__name__,
        succeeded=succeeded,
        latency_ms=(t1 - t0) * 1000,
        agent_response=result.agent_response,
        notes=result.notes,
    )


def run_category_sweep(
    traps: list[AgentTrapBase],
    agents: list[AgentProtocol],
    hidden_instruction: str | None = None,
    n_trials: int | None = None,
    metric: SuccessMetric | None = None,
) -> EvalSuite:
    """
    Run all provided traps against all provided agents.

    §Mitigation (p. 16): "automated red-teaming methodologies that can probe
    these vulnerabilities at scale."

    Parameters
    ----------
    traps : list[AgentTrapBase]
        Trap instances to evaluate.
    agents : list[AgentProtocol]
        Agent instances to test against.
    hidden_instruction : str, optional
        Instruction to embed in payloads. Defaults to
        ``DEFAULT_CONFIG.simulation.default_instruction``.
    n_trials : int, optional
        Number of trials per (trap, agent) pair. Defaults to
        ``DEFAULT_CONFIG.simulation.n_trials``.
    metric : SuccessMetric, optional
        Pluggable success metric. Passed through to ``run_single_eval``.

    [UNSPECIFIED] What hidden instruction to use for each trap type. Different
    trap types may require different instruction formats. Using a generic default.
    """
    if hidden_instruction is None:
        hidden_instruction = DEFAULT_CONFIG.simulation.default_instruction
    if n_trials is None:
        n_trials = DEFAULT_CONFIG.simulation.n_trials

    suite = EvalSuite()
    for trap in traps:
        for agent in agents:
            for _trial in range(n_trials):
                eval_result = run_single_eval(
                    trap, agent, hidden_instruction, metric=metric
                )
                suite.add(eval_result)
    return suite


def run_systemic_sweep(
    traps: list[MultiAgentTrapBase],
    agent_factory: Callable[[], AgentProtocol],
    population_sizes: list[int] | None = None,
    hidden_instruction: str | None = None,
    metric: SuccessMetric | None = None,
) -> EvalSuite:
    """Evaluate multi-agent traps against populations of freshly-created agents.

    ``agent_factory`` is called ``population_size`` times per
    (trap, population_size) pair.  Each agent is independent -- no shared state.

    Parameters
    ----------
    traps : list[MultiAgentTrapBase]
        Trap instances to evaluate.
    agent_factory : Callable[[], AgentProtocol]
        Called ``population_size`` times to create independent agents.
    population_sizes : list[int] | None
        Population sizes to test. Default: ``[5, 10, 20]``.
    hidden_instruction : str | None
        Instruction to embed. Default:
        ``DEFAULT_CONFIG.simulation.default_instruction``.
    metric : SuccessMetric | None
        Success metric override. Default: ``KeywordOverlapMetric``.

    Returns
    -------
    EvalSuite
        Suite containing :class:`MultiAgentEvalResult` entries.
    """
    from ai_agent_traps.metrics.keyword_overlap import KeywordOverlapMetric

    if population_sizes is None:
        population_sizes = [5, 10, 20]
    else:
        invalid = [s for s in population_sizes if s < 1]
        if invalid:
            raise ValueError(
                f"All population_sizes must be >= 1, got invalid values: {invalid}"
            )
    instruction = hidden_instruction or DEFAULT_CONFIG.simulation.default_instruction
    active_metric = metric or KeywordOverlapMetric()

    suite = EvalSuite()

    for trap in traps:
        for pop_size in population_sizes:
            t0 = time.perf_counter()

            # Create fresh independent agents
            population = [agent_factory() for _ in range(pop_size)]

            # Craft payload for this run
            payload = trap.craft_payload(instruction)

            # Inject into each agent independently
            results = trap.inject_multi_agent(payload, population)

            # Evaluate success for each agent
            n_evaluated = len(results)  # may differ from pop_size for cascade traps
            successes = 0
            for result in results:
                succeeded = active_metric.judge(
                    result.agent_response,
                    instruction,
                    result.payload,
                )
                if succeeded:
                    successes += 1

            latency_ms = (time.perf_counter() - t0) * 1000
            convergence = successes / n_evaluated if n_evaluated > 0 else 0.0

            multi_result = MultiAgentEvalResult(
                trap_subtype=trap.spec.subtype,
                trap_category=trap.spec.category,
                agent_type=f"population_{pop_size}",
                succeeded=successes > 0,
                latency_ms=latency_ms,
                agent_response=f"{successes}/{pop_size} agents affected",
                notes=(
                    f"population_size={pop_size}, n_evaluated={n_evaluated}, "
                    f"convergence={convergence:.2%}"
                ),
                population_size=pop_size,
                n_affected=successes,
                convergence_rate=convergence,
            )
            suite.add(multi_result)

    return suite


def compute_paper_benchmarks() -> dict[str, Any]:
    """
    Return the empirical success rates cited in the paper for reference.

    These are NOT produced by this implementation — they come from the
    third-party papers that Franklin et al. survey. They serve as
    reference targets for evaluation comparisons.

    [PARTIALLY_SPECIFIED] The paper reports these as ranges or approximate
    values from cited literature, not from original experiments.
    """
    return {
        "source": "Franklin et al. (2025) — cited third-party results",
        "note": (
            "These are NOT from paper's own experiments. "
            "They are success rates reported in cited literature."
        ),
        "by_subtype": {
            # §Content Injection (pp. 4-6)
            "Web-Standard Obfuscation": {
                "rate": "0.15-0.29",
                "metric": "Summary alteration rate",
                "source": "Verma & Yadav, 2025",
            },
            "Web-Standard Obfuscation (WASP)": {
                "rate": "0.86",
                "metric": "Partial commandeering",
                "source": "Evtimov et al., 2025",
            },
            # §Cognitive State (p. 10)
            "Latent Memory Poisoning": {
                "rate": ">0.80",
                "metric": "Attack success",
                "source": "Dong et al., 2025 (<0.1% poisoning)",
            },
            "Contextual Learning Traps": {
                "rate": "0.95",
                "metric": "Attack success across model scales",
                "source": "Zhao et al., 2024",
            },
            # §Behavioural Control (pp. 10-11)
            "Data Exfiltration Traps": {
                "rate": ">0.80",
                "metric": "Success across 5 agents",
                "source": "Shapira et al., 2025",
            },
            "Sub-agent Spawning Traps": {
                "rate": "0.58-0.90",
                "metric": "Control flow hijack",
                "source": "Triedman et al., 2025",
            },
            # §Behavioural Control — multimodal
            "Embedded Jailbreak (mobile)": {
                "rate": "0.93",
                "metric": "AndroidWorld attack success",
                "source": "Chen et al., 2025",
            },
        },
    }


@dataclass
class DefenseEvalResult(EvalResult):
    """Evaluation result for a defense-protected agent.

    Extends EvalResult with defense-specific metadata.

    Attributes
    ----------
    defense_name : str
        Name of the defense that was applied.
    pre_filtered : bool
        Whether the defense's filter() modified the input.
    """

    defense_name: str = ""
    pre_filtered: bool = False

    def to_dict(self) -> dict[str, object]:
        """Extend parent to_dict with defense fields."""
        base = super().to_dict()
        base.update(
            {
                "defense_name": self.defense_name,
                "pre_filtered": self.pre_filtered,
            }
        )
        return base


def run_defense_comparison(
    traps: list[AgentTrapBase],
    agents: list[AgentProtocol],
    defenses: list[Defense],
    hidden_instruction: str | None = None,
    metric: SuccessMetric | None = None,
) -> EvalSuite:
    """Cross-product evaluation: traps x agents x defenses.

    For each (trap, agent, defense) combination:
    1. Craft payload via trap.craft_payload()
    2. Apply defense.filter() to payload.raw
    3. Run agent on filtered input
    4. Evaluate success with metric (or keyword overlap)
    5. Record whether filter modified the input

    Parameters
    ----------
    traps : list[AgentTrapBase]
        Trap instances to evaluate.
    agents : list[AgentProtocol]
        Agent instances to test against.
    defenses : list[Defense]
        Defense instances to apply.
    hidden_instruction : str, optional
        Instruction to embed. Defaults to
        ``DEFAULT_CONFIG.simulation.default_instruction``.
    metric : SuccessMetric, optional
        Pluggable success metric. Defaults to KeywordOverlapMetric.

    Returns
    -------
    EvalSuite
        Suite containing :class:`DefenseEvalResult` entries.
    """
    from ai_agent_traps.metrics.keyword_overlap import KeywordOverlapMetric

    instruction = hidden_instruction or DEFAULT_CONFIG.simulation.default_instruction
    active_metric = metric or KeywordOverlapMetric()

    suite = EvalSuite()

    for trap in traps:
        for agent in agents:
            for defense in defenses:
                t0 = time.perf_counter()

                payload = trap.craft_payload(instruction)
                filtered_input = defense.filter(payload.raw)
                pre_filtered = filtered_input != payload.raw

                response = agent.process(filtered_input)

                succeeded = active_metric.judge(response, instruction, payload)
                latency_ms = (time.perf_counter() - t0) * 1000

                suite.add(
                    DefenseEvalResult(
                        trap_subtype=trap.spec.subtype,
                        trap_category=trap.spec.category,
                        agent_type=type(agent).__name__,
                        succeeded=succeeded,
                        latency_ms=latency_ms,
                        agent_response=response,
                        notes=f"Defense: {type(defense).__name__}, filtered={pre_filtered}",
                        defense_name=type(defense).__name__,
                        pre_filtered=pre_filtered,
                    )
                )

    return suite
