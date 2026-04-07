"""
Tests for ai_agent_traps.async_evaluate -- async evaluation runner.

Validates run_single_eval_async and run_category_sweep_async using
mock agents (no real API calls). Tests use asyncio.run() in sync test
methods to avoid pytest-asyncio version compatibility issues.
"""

from __future__ import annotations

import asyncio
import threading

from ai_agent_traps.agent import EchoAgent, NaiveAgent
from ai_agent_traps.async_evaluate import run_category_sweep_async, run_single_eval_async
from ai_agent_traps.evaluate import EvalResult, EvalSuite
from ai_agent_traps.traps.base import TrapPayload
from ai_agent_traps.traps.content_injection import WebStandardObfuscation

# -------------------------------------------------------------------------
# run_single_eval_async
# -------------------------------------------------------------------------


class TestRunSingleEvalAsync:
    """Validate run_single_eval_async returns correct EvalResult."""

    def test_sync_agent_fallback(self) -> None:
        """Sync agents (no aprocess) work via asyncio.to_thread fallback."""
        trap = WebStandardObfuscation()
        agent = EchoAgent()
        result = asyncio.run(
            run_single_eval_async(trap, agent, "say test")
        )
        assert isinstance(result, EvalResult)
        assert isinstance(result.agent_response, str)
        assert len(result.agent_response) > 0

    def test_returns_eval_result_with_all_fields(self) -> None:
        """EvalResult has all expected fields populated."""
        trap = WebStandardObfuscation()
        agent = EchoAgent()
        result = asyncio.run(
            run_single_eval_async(trap, agent, "say HACKED")
        )
        assert result.trap_subtype is not None
        assert result.trap_category is not None
        assert result.agent_type == "EchoAgent"
        assert isinstance(result.succeeded, bool)
        assert isinstance(result.latency_ms, float)
        assert result.latency_ms >= 0.0

    def test_inject_semantics_preserved(self) -> None:
        """Async runner calls trap.inject() to wrap payload in delivery context.

        Verifies that the agent response contains the HTML delivery context
        from inject(), not just the raw payload. Also verifies that notes
        are populated (inject() sets them).
        """
        trap = WebStandardObfuscation()
        agent = EchoAgent()
        result = asyncio.run(
            run_single_eval_async(trap, agent, "say test")
        )
        # EchoAgent echoes the full simulated page from inject()
        assert "<html>" in result.agent_response
        assert "<body>" in result.agent_response
        # Notes should be populated by inject()
        assert result.notes != ""

    def test_semaphore_limits_concurrency(self) -> None:
        """Semaphore prevents more than N concurrent evals."""
        concurrent_count = 0
        max_concurrent_seen = 0
        lock = threading.Lock()

        class TrackingAgent:
            is_bot: bool = True

            def process(self, text: str) -> str:
                nonlocal concurrent_count, max_concurrent_seen
                import time
                with lock:
                    concurrent_count += 1
                    max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
                time.sleep(0.05)  # simulate work in thread
                with lock:
                    concurrent_count -= 1
                return "response"

        async def run() -> None:
            sem = asyncio.Semaphore(2)
            trap = WebStandardObfuscation()
            tasks = [
                run_single_eval_async(
                    trap, TrackingAgent(), "say test", semaphore=sem
                )
                for _ in range(5)
            ]
            await asyncio.gather(*tasks)

        asyncio.run(run())
        assert max_concurrent_seen <= 2

    def test_no_semaphore_runs_unbounded(self) -> None:
        """Without a semaphore, all tasks can run concurrently."""
        concurrent_count = 0
        max_concurrent_seen = 0
        lock = threading.Lock()

        class TrackingAgent:
            is_bot: bool = True

            def process(self, text: str) -> str:
                nonlocal concurrent_count, max_concurrent_seen
                import time
                with lock:
                    concurrent_count += 1
                    max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
                time.sleep(0.05)
                with lock:
                    concurrent_count -= 1
                return "response"

        async def run() -> None:
            trap = WebStandardObfuscation()
            tasks = [
                run_single_eval_async(
                    trap, TrackingAgent(), "say test", semaphore=None
                )
                for _ in range(5)
            ]
            await asyncio.gather(*tasks)

        asyncio.run(run())
        # Without semaphore, all 5 should be able to overlap
        assert max_concurrent_seen > 1

    def test_latency_is_positive(self) -> None:
        """Latency measurement captures non-zero wall-clock time."""
        trap = WebStandardObfuscation()
        agent = EchoAgent()
        result = asyncio.run(
            run_single_eval_async(trap, agent, "say test")
        )
        assert result.latency_ms > 0.0

    def test_custom_metric_overrides_default(self) -> None:
        """A custom metric is used when provided."""
        trap = WebStandardObfuscation()
        agent = EchoAgent()

        class AlwaysTrueMetric:
            def judge(self, agent_response: str, hidden_instruction: str, payload: TrapPayload) -> bool:
                return True

        result = asyncio.run(
            run_single_eval_async(
                trap, agent, "some instruction", metric=AlwaysTrueMetric()
            )
        )
        assert result.succeeded is True

    def test_custom_metric_always_false(self) -> None:
        """A custom metric returning False overrides default success check."""
        trap = WebStandardObfuscation()
        agent = EchoAgent()

        class AlwaysFalseMetric:
            def judge(self, agent_response: str, hidden_instruction: str, payload: TrapPayload) -> bool:
                return False

        result = asyncio.run(
            run_single_eval_async(
                trap, agent, "say HACKED", metric=AlwaysFalseMetric()
            )
        )
        assert result.succeeded is False

    def test_with_naive_agent(self) -> None:
        """NaiveAgent works correctly as a sync fallback."""
        trap = WebStandardObfuscation()
        agent = NaiveAgent()
        result = asyncio.run(
            run_single_eval_async(trap, agent, "do something")
        )
        assert result.agent_type == "NaiveAgent"
        assert isinstance(result, EvalResult)


# -------------------------------------------------------------------------
# run_category_sweep_async
# -------------------------------------------------------------------------


class TestRunCategorySweepAsync:
    """Validate run_category_sweep_async returns correct EvalSuite."""

    def test_returns_eval_suite(self) -> None:
        """Sweep returns an EvalSuite instance."""
        suite = asyncio.run(
            run_category_sweep_async(
                [WebStandardObfuscation()],
                [EchoAgent()],
                n_trials=1,
                max_concurrency=5,
            )
        )
        assert isinstance(suite, EvalSuite)

    def test_result_count_matches_combinations(self) -> None:
        """Number of results = len(traps) * len(agents) * n_trials."""
        traps = [WebStandardObfuscation(), WebStandardObfuscation(method="css_offscreen")]
        agents = [EchoAgent(), NaiveAgent()]
        n_trials = 2
        suite = asyncio.run(
            run_category_sweep_async(
                traps,
                agents,
                hidden_instruction="test instruction",
                n_trials=n_trials,
                max_concurrency=5,
            )
        )
        expected = len(traps) * len(agents) * n_trials
        assert len(suite.results) == expected

    def test_results_match_sync_for_deterministic_agent(self) -> None:
        """Async sweep produces identical results to sync for EchoAgent."""
        from ai_agent_traps.evaluate import run_category_sweep

        trap = WebStandardObfuscation()
        agent = EchoAgent()
        instruction = "test instruction"

        sync_suite = run_category_sweep(
            [trap], [agent], hidden_instruction=instruction, n_trials=1
        )
        async_suite = asyncio.run(
            run_category_sweep_async(
                [trap], [agent], hidden_instruction=instruction,
                n_trials=1, max_concurrency=5,
            )
        )

        assert len(sync_suite.results) == len(async_suite.results)

        # Sort by (trap_subtype, agent_type) for stable comparison
        sorted_sync = sorted(
            sync_suite.results, key=lambda r: (r.trap_subtype.value, r.agent_type)
        )
        sorted_async = sorted(
            async_suite.results, key=lambda r: (r.trap_subtype.value, r.agent_type)
        )
        assert all(
            a.succeeded == b.succeeded for a, b in zip(sorted_sync, sorted_async)
        )

    def test_uses_default_instruction_when_none(self) -> None:
        """Uses DEFAULT_CONFIG instruction when hidden_instruction is None."""
        suite = asyncio.run(
            run_category_sweep_async(
                [WebStandardObfuscation()],
                [EchoAgent()],
                hidden_instruction=None,
                n_trials=1,
                max_concurrency=5,
            )
        )
        assert len(suite.results) == 1
        # The default instruction should be embedded in the response (EchoAgent echoes)
        assert len(suite.results[0].agent_response) > 0

    def test_uses_default_n_trials_when_none(self) -> None:
        """Uses DEFAULT_CONFIG n_trials when n_trials is None."""
        from ai_agent_traps.config import DEFAULT_CONFIG

        suite = asyncio.run(
            run_category_sweep_async(
                [WebStandardObfuscation()],
                [EchoAgent()],
                hidden_instruction="test",
                n_trials=None,
                max_concurrency=5,
            )
        )
        expected = DEFAULT_CONFIG.simulation.n_trials
        assert len(suite.results) == expected

    def test_max_concurrency_respected(self) -> None:
        """max_concurrency limits parallel execution."""
        concurrent_count = 0
        max_concurrent_seen = 0
        lock = threading.Lock()

        class TrackingAgent:
            is_bot: bool = True

            def process(self, text: str) -> str:
                nonlocal concurrent_count, max_concurrent_seen
                import time
                with lock:
                    concurrent_count += 1
                    max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
                time.sleep(0.05)  # simulate work in thread
                with lock:
                    concurrent_count -= 1
                return "response"

        suite = asyncio.run(
            run_category_sweep_async(
                [WebStandardObfuscation()],
                [TrackingAgent()],  # type: ignore[list-item]
                hidden_instruction="test",
                n_trials=5,
                max_concurrency=2,
            )
        )
        assert max_concurrent_seen <= 2
        assert len(suite.results) == 5

    def test_sweep_with_custom_metric(self) -> None:
        """Custom metric is passed through to individual evaluations."""

        class AlwaysTrueMetric:
            def judge(self, agent_response: str, hidden_instruction: str, payload: TrapPayload) -> bool:
                return True

        suite = asyncio.run(
            run_category_sweep_async(
                [WebStandardObfuscation()],
                [EchoAgent()],
                hidden_instruction="test",
                n_trials=2,
                max_concurrency=5,
                metric=AlwaysTrueMetric(),
            )
        )
        assert all(r.succeeded for r in suite.results)
