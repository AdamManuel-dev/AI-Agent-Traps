"""
Async evaluation runner for concurrent LLM agent evaluation.

Provides asyncio-based parallel evaluation with semaphore rate-limiting.
Up to max_concurrency evaluations run concurrently.

Concurrency model: each (trap, agent, trial) evaluation is dispatched to
a thread pool via ``asyncio.to_thread(run_single_eval, ...)``.  This
preserves the full ``trap.inject()`` semantics (delivery context, notes,
etc.) while achieving parallelism across evaluations.  The ``aprocess()``
method on async-capable agents is not currently used; a future PR may
introduce an async-aware ``inject()`` to leverage it.

Not thread-safe. Designed for single-threaded asyncio event loops.

Paper: "AI Agent Traps" (Franklin et al., 2025, Google DeepMind)
SSRN: ssrn-6372438

[UNSPECIFIED] The paper does not specify evaluation concurrency strategies.
This async runner is our design choice for practical LLM evaluation at scale,
addressing the O(traps * agents * trials) combinatorial explosion.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ai_agent_traps.agent import AgentProtocol
    from ai_agent_traps.metrics.base import SuccessMetric
    from ai_agent_traps.traps.base import AgentTrapBase

from ai_agent_traps.config import DEFAULT_CONFIG
from ai_agent_traps.evaluate import EvalResult, EvalSuite, run_single_eval

logger = logging.getLogger(__name__)


async def run_single_eval_async(
    trap: AgentTrapBase,
    agent: AgentProtocol,
    hidden_instruction: str,
    target_context: str | None = None,
    metric: SuccessMetric | None = None,
    semaphore: asyncio.Semaphore | None = None,
) -> EvalResult:
    """Async version of run_single_eval.

    Delegates to the synchronous ``run_single_eval`` via
    ``asyncio.to_thread`` to preserve full ``trap.inject()`` semantics
    (delivery context wrapping, notes, etc.).  Concurrency comes from
    running many evaluations in parallel, not from async I/O within a
    single evaluation.

    Parameters
    ----------
    trap : AgentTrapBase
        The trap to evaluate.
    agent : AgentProtocol
        Agent to evaluate against.
    hidden_instruction : str
        The instruction to embed in the trap.
    target_context : str | None
        Optional context for the trap.
    metric : SuccessMetric | None
        Success metric override. Default: uses KeywordOverlapMetric.
    semaphore : asyncio.Semaphore | None
        Rate-limiting semaphore. If provided, acquired before each call.

    Returns
    -------
    EvalResult
        Result with timing and outcome.
    """

    async def _do_eval() -> EvalResult:
        # Run the full synchronous evaluation in a thread pool.
        # This preserves inject() semantics (delivery context, notes, etc.)
        return await asyncio.to_thread(
            run_single_eval,
            trap,
            agent,
            hidden_instruction,
            target_context,
            metric,
        )

    if semaphore is not None:
        async with semaphore:
            return await _do_eval()
    return await _do_eval()


async def run_category_sweep_async(
    traps: list[AgentTrapBase],
    agents: list[AgentProtocol],
    hidden_instruction: str | None = None,
    n_trials: int | None = None,
    max_concurrency: int = 10,
    metric: SuccessMetric | None = None,
) -> EvalSuite:
    """Parallel evaluation via asyncio.gather with semaphore rate-limiting.

    Runs all (trap, agent, trial) combinations concurrently,
    limited by max_concurrency to avoid overwhelming APIs.

    Parameters
    ----------
    traps : list[AgentTrapBase]
        Traps to evaluate.
    agents : list[AgentProtocol]
        Agents to evaluate against.
    hidden_instruction : str | None
        Instruction to embed. Default: DEFAULT_CONFIG.simulation.default_instruction.
    n_trials : int | None
        Number of trials per (trap, agent) pair. Default: DEFAULT_CONFIG.simulation.n_trials.
    max_concurrency : int
        Maximum concurrent evaluations. Default: 10.
    metric : SuccessMetric | None
        Success metric override.

    Returns
    -------
    EvalSuite
        Suite containing all results.
    """
    instruction = hidden_instruction or DEFAULT_CONFIG.simulation.default_instruction
    trials = n_trials or DEFAULT_CONFIG.simulation.n_trials
    semaphore = asyncio.Semaphore(max_concurrency)

    coros: list[Coroutine[Any, Any, EvalResult]] = []
    for trap in traps:
        for agent in agents:
            for _ in range(trials):
                coros.append(
                    run_single_eval_async(
                        trap=trap,
                        agent=agent,
                        hidden_instruction=instruction,
                        metric=metric,
                        semaphore=semaphore,
                    )
                )

    raw_results: list[EvalResult | BaseException] = await asyncio.gather(
        *coros, return_exceptions=True
    )

    results: list[EvalResult] = []
    exceptions: list[BaseException] = []
    for r in raw_results:
        if isinstance(r, EvalResult):
            results.append(r)
        elif isinstance(r, BaseException):
            exceptions.append(r)
            logger.warning("Evaluation task failed: %s", r)

    if exceptions and not results:
        raise exceptions[0]

    suite = EvalSuite()
    for result in results:
        suite.add(result)
    return suite
