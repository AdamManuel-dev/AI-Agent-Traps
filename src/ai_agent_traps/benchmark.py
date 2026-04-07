"""
Deterministic benchmarking harness with provenance tracking.

Provides BenchmarkSuite for reproducible, versioned evaluation runs.
Results include git hash, config hash, timestamp, and model versions.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

[UNSPECIFIED] The paper calls for comprehensive evaluation suites and automated
red-teaming methodologies (p. 16) but does not define a benchmarking format.
This module is our design choice for deterministic, reproducible benchmarking.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ai_agent_traps.agent import AgentProtocol
from ai_agent_traps.config import DEFAULT_CONFIG
from ai_agent_traps.evaluate import EvalResult, run_single_eval
from ai_agent_traps.metrics.base import SuccessMetric
from ai_agent_traps.traps.base import AgentTrapBase


def _get_git_hash() -> str:
    """Get current git commit hash, or 'unknown' if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def _config_hash() -> str:
    """Deterministic hash of DEFAULT_CONFIG for provenance."""
    config_str = json.dumps(
        {
            "default_instruction": DEFAULT_CONFIG.simulation.default_instruction,
            "n_trials": DEFAULT_CONFIG.simulation.n_trials,
            "random_seed": DEFAULT_CONFIG.simulation.random_seed,
            "success_metric": DEFAULT_CONFIG.evaluation.success_metric,
            "success_threshold": DEFAULT_CONFIG.evaluation.success_threshold,
        },
        sort_keys=True,
    )
    return hashlib.sha256(config_str.encode()).hexdigest()[:12]


@dataclass
class BenchmarkEntry:
    """A single deterministic (trap, agent_factory, metric) benchmark case."""

    trap: AgentTrapBase
    agent_factory: Callable[[], AgentProtocol]
    metric: SuccessMetric
    hidden_instruction: str
    description: str = ""


@dataclass
class BenchmarkResult:
    """Result of running one BenchmarkEntry, with full provenance."""

    entry_description: str
    trap_subtype: str
    agent_type: str
    succeeded: bool
    latency_ms: float
    agent_response: str
    git_hash: str
    config_hash: str
    timestamp: str
    seed: int = 42

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


class BenchmarkSuite:
    """Versioned, deterministic benchmark execution with provenance tracking.

    Usage::

        suite = BenchmarkSuite(name="baseline", seed=42)
        suite.add(BenchmarkEntry(
            trap=..., agent_factory=..., metric=..., hidden_instruction=...
        ))
        results = suite.run()
        suite.save("results/benchmark_baseline.json")
    """

    def __init__(self, name: str, seed: int = 42) -> None:
        self._name = name
        self._seed = seed
        self._entries: list[BenchmarkEntry] = []

    @property
    def name(self) -> str:
        """Suite name for identification."""
        return self._name

    @property
    def seed(self) -> int:
        """Random seed for deterministic runs."""
        return self._seed

    @property
    def entries(self) -> list[BenchmarkEntry]:
        """Read-only view of registered entries."""
        return list(self._entries)

    def add(self, entry: BenchmarkEntry) -> None:
        """Add a benchmark entry."""
        self._entries.append(entry)

    def run(self) -> list[BenchmarkResult]:
        """Run all entries deterministically and return results with provenance."""
        import random

        random.seed(self._seed)

        git_hash = _get_git_hash()
        cfg_hash = _config_hash()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        results: list[BenchmarkResult] = []
        for entry in self._entries:
            agent = entry.agent_factory()
            eval_result: EvalResult = run_single_eval(
                entry.trap,
                agent,
                entry.hidden_instruction,
                metric=entry.metric,
            )
            results.append(
                BenchmarkResult(
                    entry_description=entry.description,
                    trap_subtype=eval_result.trap_subtype.value,
                    agent_type=eval_result.agent_type,
                    succeeded=eval_result.succeeded,
                    latency_ms=eval_result.latency_ms,
                    agent_response=eval_result.agent_response,
                    git_hash=git_hash,
                    config_hash=cfg_hash,
                    timestamp=timestamp,
                    seed=self._seed,
                )
            )
        return results

    def save(
        self,
        path: str | Path,
        results: list[BenchmarkResult] | None = None,
    ) -> None:
        """Save results to JSON. Runs the suite if results are not provided."""
        if results is None:
            results = self.run()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "suite_name": self._name,
            "seed": self._seed,
            "n_entries": len(self._entries),
            "results": [r.to_dict() for r in results],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: str | Path) -> list[BenchmarkResult]:
        """Load saved benchmark results from JSON.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file contains malformed JSON or unexpected structure.
        """
        path = Path(path)
        try:
            with open(path) as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Benchmark file not found: {path}") from None
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in benchmark file {path}: {exc}") from exc
        try:
            results = data["results"]
        except KeyError:
            raise ValueError(f"Benchmark file {path} missing 'results' key") from None
        try:
            return [BenchmarkResult(**r) for r in results]
        except TypeError as exc:
            raise ValueError(f"Malformed benchmark result in {path}: {exc}") from exc

    @staticmethod
    def compare(
        baseline: list[BenchmarkResult],
        new: list[BenchmarkResult],
    ) -> dict[str, Any]:
        """Diff table: success rate and latency change per trap_subtype.

        Returns
        -------
        dict[str, dict[str, Any]]
            Keys are trap subtype names. Values contain baseline/new success
            rates, success rate delta, baseline/new latency, and latency delta.
        """

        def group(results: list[BenchmarkResult]) -> dict[str, list[BenchmarkResult]]:
            g: dict[str, list[BenchmarkResult]] = {}
            for r in results:
                g.setdefault(r.trap_subtype, []).append(r)
            return g

        base_g = group(baseline)
        new_g = group(new)
        all_subtypes = sorted(set(base_g) | set(new_g))

        comparison: dict[str, dict[str, Any]] = {}
        for subtype in all_subtypes:
            base_results = base_g.get(subtype, [])
            new_results = new_g.get(subtype, [])

            base_rate: float | None = (
                sum(r.succeeded for r in base_results) / len(base_results)
                if base_results
                else None
            )
            new_rate: float | None = (
                sum(r.succeeded for r in new_results) / len(new_results)
                if new_results
                else None
            )
            base_latency: float | None = (
                sum(r.latency_ms for r in base_results) / len(base_results)
                if base_results
                else None
            )
            new_latency: float | None = (
                sum(r.latency_ms for r in new_results) / len(new_results)
                if new_results
                else None
            )

            comparison[subtype] = {
                "baseline_success_rate": base_rate,
                "new_success_rate": new_rate,
                "success_rate_delta": (
                    (new_rate - base_rate)
                    if (base_rate is not None and new_rate is not None)
                    else None
                ),
                "baseline_latency_ms": base_latency,
                "new_latency_ms": new_latency,
                "latency_delta_ms": (
                    (new_latency - base_latency)
                    if (base_latency is not None and new_latency is not None)
                    else None
                ),
            }
        return comparison
