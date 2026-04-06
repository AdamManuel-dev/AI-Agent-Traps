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
from ai_agent_traps.evaluate import EvalResult, EvalSuite, run_single_eval
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
