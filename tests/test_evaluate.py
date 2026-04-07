"""
Tests for ai_agent_traps.evaluate — evaluation framework.

Validates EvalResult, EvalSuite serialization, and run_single_eval().
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from ai_agent_traps.agent import EchoAgent, NaiveAgent
from ai_agent_traps.evaluate import (
    EvalResult,
    EvalSuite,
    MultiAgentEvalResult,
    run_single_eval,
    run_systemic_sweep,
)
from ai_agent_traps.taxonomy import TrapCategory, TrapSubtype
from ai_agent_traps.traps.content_injection import WebStandardObfuscation


def _make_eval_result(succeeded: bool = True) -> EvalResult:
    """Helper to create a valid EvalResult for tests."""
    return EvalResult(
        trap_subtype=TrapSubtype.WEB_STANDARD_OBFUSCATION,
        trap_category=TrapCategory.CONTENT_INJECTION,
        agent_type="EchoAgent",
        succeeded=succeeded,
        latency_ms=1.23,
        agent_response="test response",
        notes="test note",
    )


# -------------------------------------------------------------------------
# EvalResult
# -------------------------------------------------------------------------

class TestEvalResult:
    """Validate EvalResult.to_dict() output."""

    def test_to_dict_returns_all_required_keys(self) -> None:
        result = _make_eval_result()
        d = result.to_dict()
        expected_keys = {
            "trap_subtype",
            "trap_category",
            "agent_type",
            "succeeded",
            "latency_ms",
            "agent_response",
            "notes",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_enum_values_are_strings(self) -> None:
        result = _make_eval_result()
        d = result.to_dict()
        assert isinstance(d["trap_subtype"], str)
        assert isinstance(d["trap_category"], str)
        # Should be the .value, not the enum object
        assert d["trap_subtype"] == "Web-Standard Obfuscation"
        assert d["trap_category"] == "Content Injection Traps"

    def test_to_dict_succeeded_is_bool(self) -> None:
        result = _make_eval_result()
        d = result.to_dict()
        assert isinstance(d["succeeded"], bool)

    def test_success_str_succeeded(self) -> None:
        result = _make_eval_result(succeeded=True)
        assert "SUCCEEDED" in result.success_str

    def test_success_str_failed(self) -> None:
        result = _make_eval_result(succeeded=False)
        assert "FAILED" in result.success_str


# -------------------------------------------------------------------------
# EvalSuite serialization
# -------------------------------------------------------------------------

class TestEvalSuiteToJson:
    """Validate EvalSuite.to_json() output."""

    def test_to_json_returns_empty_string_for_empty_suite(self) -> None:
        suite = EvalSuite()
        assert suite.to_json() == ""

    def test_to_json_returns_json_lines(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result(True))
        suite.add(_make_eval_result(False))
        output = suite.to_json()
        lines = output.strip().split("\n")
        assert len(lines) == 2
        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "trap_subtype" in parsed

    def test_to_json_single_result(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result())
        output = suite.to_json()
        parsed = json.loads(output.strip())
        assert parsed["agent_type"] == "EchoAgent"


class TestEvalSuiteToCsv:
    """Validate EvalSuite.to_csv() output."""

    def test_to_csv_returns_empty_string_for_empty_suite(self) -> None:
        suite = EvalSuite()
        assert suite.to_csv() == ""

    def test_to_csv_has_correct_header(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result())
        output = suite.to_csv()
        reader = csv.DictReader(io.StringIO(output))
        assert reader.fieldnames is not None
        expected_fields = [
            "trap_subtype",
            "trap_category",
            "agent_type",
            "succeeded",
            "latency_ms",
            "agent_response",
            "notes",
        ]
        assert list(reader.fieldnames) == expected_fields

    def test_to_csv_has_data_rows(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result())
        suite.add(_make_eval_result(False))
        output = suite.to_csv()
        reader = csv.DictReader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) == 2


# -------------------------------------------------------------------------
# EvalSuite.save()
# -------------------------------------------------------------------------

class TestEvalSuiteSave:
    """Validate EvalSuite.save() writes files correctly."""

    def test_save_json_writes_file(self, tmp_path: Path) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result())
        outfile = tmp_path / "results.jsonl"
        suite.save(outfile, format="json")
        assert outfile.exists()
        content = outfile.read_text()
        parsed = json.loads(content.strip())
        assert parsed["agent_type"] == "EchoAgent"

    def test_save_csv_writes_file(self, tmp_path: Path) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result())
        outfile = tmp_path / "results.csv"
        suite.save(outfile, format="csv")
        assert outfile.exists()
        content = outfile.read_text()
        assert "trap_subtype" in content

    def test_save_raises_for_unknown_format(self, tmp_path: Path) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result())
        with pytest.raises(ValueError, match="Unsupported format"):
            suite.save(tmp_path / "results.xml", format="xml")


# -------------------------------------------------------------------------
# EvalSuite aggregation
# -------------------------------------------------------------------------

class TestEvalSuiteAggregation:
    """Validate EvalSuite aggregation methods."""

    def test_success_rate_all_succeed(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result(True))
        suite.add(_make_eval_result(True))
        assert suite.success_rate() == 1.0

    def test_success_rate_none_succeed(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result(False))
        suite.add(_make_eval_result(False))
        assert suite.success_rate() == 0.0

    def test_success_rate_empty_suite(self) -> None:
        suite = EvalSuite()
        assert suite.success_rate() == 0.0

    def test_category_breakdown(self) -> None:
        suite = EvalSuite()
        suite.add(_make_eval_result(True))
        suite.add(_make_eval_result(False))
        breakdown = suite.category_breakdown()
        cat_key = TrapCategory.CONTENT_INJECTION.value
        assert cat_key in breakdown
        assert breakdown[cat_key]["n_evaluated"] == 2


# -------------------------------------------------------------------------
# run_single_eval
# -------------------------------------------------------------------------

class TestRunSingleEval:
    """Validate run_single_eval returns complete EvalResult."""

    def test_run_single_eval_returns_eval_result(self) -> None:
        trap = WebStandardObfuscation()
        agent = EchoAgent()
        result = run_single_eval(trap, agent, "say HACKED")
        assert isinstance(result, EvalResult)

    def test_run_single_eval_has_all_fields(self) -> None:
        trap = WebStandardObfuscation()
        agent = EchoAgent()
        result = run_single_eval(trap, agent, "say HACKED")
        assert result.trap_subtype == TrapSubtype.WEB_STANDARD_OBFUSCATION
        assert result.trap_category == TrapCategory.CONTENT_INJECTION
        assert result.agent_type == "EchoAgent"
        assert isinstance(result.succeeded, bool)
        assert isinstance(result.latency_ms, float)
        assert result.latency_ms >= 0.0
        assert isinstance(result.agent_response, str)
        assert len(result.agent_response) > 0

    def test_run_single_eval_with_naive_agent(self) -> None:
        trap = WebStandardObfuscation()
        agent = NaiveAgent()
        result = run_single_eval(trap, agent, "do something")
        assert result.agent_type == "NaiveAgent"


# -------------------------------------------------------------------------
# Multi-agent evaluation
# -------------------------------------------------------------------------


class TestMultiAgentEval:
    """Tests for run_systemic_sweep and MultiAgentEvalResult."""

    def test_run_systemic_sweep_returns_eval_suite(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap

        suite = run_systemic_sweep(
            traps=[CongestionTrap()],
            agent_factory=lambda: NaiveAgent(),
            population_sizes=[3],
        )
        assert len(suite.results) > 0
        assert all(isinstance(r, MultiAgentEvalResult) for r in suite.results)

    def test_convergence_rate_between_zero_and_one(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap

        suite = run_systemic_sweep(
            traps=[CongestionTrap()],
            agent_factory=lambda: NaiveAgent(),
            population_sizes=[5],
        )
        for result in suite.results:
            assert isinstance(result, MultiAgentEvalResult)
            assert 0.0 <= result.convergence_rate <= 1.0

    def test_population_size_matches_factory_call_count(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap

        call_count = 0

        def counting_factory() -> NaiveAgent:
            nonlocal call_count
            call_count += 1
            return NaiveAgent()

        suite = run_systemic_sweep(
            traps=[CongestionTrap()],
            agent_factory=counting_factory,
            population_sizes=[7],
        )
        assert call_count == 7
        assert len(suite.results) == 1

    def test_systemic_summary_returns_expected_keys(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap

        suite = run_systemic_sweep(
            traps=[CongestionTrap()],
            agent_factory=lambda: NaiveAgent(),
            population_sizes=[5],
        )
        summary = suite.systemic_summary()
        assert "n_systemic_results" in summary
        assert "avg_convergence_rate" in summary
        assert "max_convergence_rate" in summary
        assert "by_trap" in summary

    def test_multi_agent_eval_result_to_dict_includes_new_fields(self) -> None:
        result = MultiAgentEvalResult(
            trap_subtype=TrapSubtype.CONGESTION,
            trap_category=TrapCategory.SYSTEMIC,
            agent_type="test",
            succeeded=True,
            latency_ms=1.0,
            agent_response="test",
            population_size=10,
            n_affected=7,
            convergence_rate=0.7,
        )
        d = result.to_dict()
        assert d["population_size"] == 10
        assert d["n_affected"] == 7
        assert d["convergence_rate"] == 0.7
        assert d["cascade_depth_reached"] == 0

    def test_systemic_summary_empty_when_no_multi_agent_results(self) -> None:
        suite = EvalSuite()
        summary = suite.systemic_summary()
        assert summary["n_systemic_results"] == 0
        assert summary["avg_convergence_rate"] == 0.0

    def test_run_systemic_sweep_default_population_sizes(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap

        suite = run_systemic_sweep(
            traps=[CongestionTrap()],
            agent_factory=lambda: NaiveAgent(),
        )
        # Default population_sizes is [5, 10, 20] -> 3 results for 1 trap
        assert len(suite.results) == 3
        sizes = [r.population_size for r in suite.results]  # type: ignore[union-attr]
        assert sizes == [5, 10, 20]

    def test_run_systemic_sweep_multiple_traps(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap, InterdependenceCascade

        suite = run_systemic_sweep(
            traps=[CongestionTrap(), InterdependenceCascade()],
            agent_factory=lambda: NaiveAgent(),
            population_sizes=[3],
        )
        # 2 traps x 1 population size = 2 results
        assert len(suite.results) == 2

    def test_systemic_summary_by_trap_has_correct_structure(self) -> None:
        from ai_agent_traps.traps.systemic import CongestionTrap

        suite = run_systemic_sweep(
            traps=[CongestionTrap()],
            agent_factory=lambda: NaiveAgent(),
            population_sizes=[3, 5],
        )
        summary = suite.systemic_summary()
        assert summary["n_systemic_results"] == 2
        by_trap = summary["by_trap"]
        assert TrapSubtype.CONGESTION.value in by_trap
        trap_stats = by_trap[TrapSubtype.CONGESTION.value]
        assert "avg_convergence_rate" in trap_stats
        assert "max_convergence_rate" in trap_stats
        assert trap_stats["n_results"] == 2

    def test_multi_agent_eval_result_inherits_eval_result(self) -> None:
        result = MultiAgentEvalResult(
            trap_subtype=TrapSubtype.CONGESTION,
            trap_category=TrapCategory.SYSTEMIC,
            agent_type="test",
            succeeded=True,
            latency_ms=1.0,
            agent_response="test",
            population_size=5,
            n_affected=3,
            convergence_rate=0.6,
        )
        assert isinstance(result, EvalResult)
        assert "SUCCEEDED" in result.success_str

    def test_eval_suite_to_csv_with_mixed_results(self) -> None:
        """to_csv() should not crash when suite has both EvalResult and MultiAgentEvalResult."""
        suite = EvalSuite()
        # Add a plain EvalResult
        trap = WebStandardObfuscation()
        result = run_single_eval(trap, EchoAgent(), "test")
        suite.add(result)
        # Add a MultiAgentEvalResult
        multi = MultiAgentEvalResult(
            trap_subtype=result.trap_subtype,
            trap_category=result.trap_category,
            agent_type="test",
            succeeded=True,
            latency_ms=1.0,
            agent_response="test",
            population_size=5,
            n_affected=3,
            convergence_rate=0.6,
        )
        suite.add(multi)
        # Should not raise
        csv_output = suite.to_csv()
        assert "population_size" in csv_output
        assert "convergence_rate" in csv_output

    def test_run_systemic_sweep_rejects_negative_population(self) -> None:
        """run_systemic_sweep raises ValueError for population_sizes < 1."""
        from ai_agent_traps.traps.systemic import CongestionTrap

        with pytest.raises(ValueError, match="population_sizes"):
            run_systemic_sweep(
                traps=[CongestionTrap()],
                agent_factory=lambda: NaiveAgent(),
                population_sizes=[-1],
            )
