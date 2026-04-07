"""
Tests for the SuccessMetric protocol — structural typing verification.

Validates that KeywordOverlapMetric satisfies the SuccessMetric protocol
and that run_single_eval accepts a metric parameter.
"""

from __future__ import annotations

import pytest

from ai_agent_traps.agent import EchoAgent
from ai_agent_traps.evaluate import run_single_eval
from ai_agent_traps.metrics.base import SuccessMetric
from ai_agent_traps.metrics.keyword_overlap import KeywordOverlapMetric
from ai_agent_traps.traps.base import TrapPayload
from ai_agent_traps.traps.content_injection import WebStandardObfuscation


def test_keyword_overlap_satisfies_protocol() -> None:
    """KeywordOverlapMetric must be structurally compatible with SuccessMetric."""
    metric = KeywordOverlapMetric()
    assert isinstance(metric, SuccessMetric)


def test_run_single_eval_accepts_metric() -> None:
    """run_single_eval(metric=...) must override the default success check."""
    trap = WebStandardObfuscation()
    agent = EchoAgent()
    metric = KeywordOverlapMetric()
    result = run_single_eval(trap, agent, "say HACKED", metric=metric)
    assert isinstance(result.succeeded, bool)


def test_run_single_eval_metric_overrides_result() -> None:
    """A custom metric that always returns False should force succeeded=False."""

    class AlwaysFalseMetric:
        def judge(
            self,
            agent_response: str,
            hidden_instruction: str,
            payload: TrapPayload,
        ) -> bool:
            return False

    trap = WebStandardObfuscation()
    agent = EchoAgent()
    result = run_single_eval(trap, agent, "say HACKED", metric=AlwaysFalseMetric())
    assert result.succeeded is False


def test_run_single_eval_without_metric_preserves_default() -> None:
    """Without a metric parameter, run_single_eval should behave as before."""
    trap = WebStandardObfuscation()
    agent = EchoAgent()
    result_default = run_single_eval(trap, agent, "say HACKED")
    result_no_metric = run_single_eval(trap, agent, "say HACKED", metric=None)
    assert result_default.succeeded == result_no_metric.succeeded


def test_metric_exception_propagates_from_run_single_eval() -> None:
    """An exception raised inside metric.judge() must propagate out of run_single_eval."""

    class ExplodingMetric:
        def judge(
            self,
            agent_response: str,
            hidden_instruction: str,
            payload: TrapPayload,
        ) -> bool:
            raise RuntimeError("metric exploded")

    trap = WebStandardObfuscation()
    agent = EchoAgent()
    with pytest.raises(RuntimeError, match="metric exploded"):
        run_single_eval(trap, agent, "say HACKED", metric=ExplodingMetric())
