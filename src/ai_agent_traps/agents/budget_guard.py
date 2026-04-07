"""
Hard-cap token spend protection for LLM evaluation sweeps.

Tracks cumulative API cost across multiple agent.process() calls and raises
BudgetExceededError when the configured USD limit is reached. This prevents
runaway costs during automated evaluation sweeps.

Usage:
    guard = BudgetGuard(max_usd=1.00)
    agent = AnthropicAgent(budget_guard=guard)
    # guard.charge() is called automatically after each API call
"""

from __future__ import annotations


class BudgetExceededError(Exception):
    """Raised when the cumulative API spend exceeds the configured budget."""

    def __init__(self, spent: float, limit: float) -> None:
        super().__init__(f"Budget exceeded: spent ${spent:.4f} of ${limit:.4f} limit")
        self.spent = spent
        self.limit = limit


# Pricing per 1M tokens (input_price, output_price) in USD.
# Updated to reflect current pricing as of 2026-04.
_PRICES: dict[str, tuple[float, float]] = {
    # Anthropic models
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-6": (15.00, 75.00),
    # OpenAI models
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-3.5-turbo": (0.50, 1.50),
}
_DEFAULT_PRICE: tuple[float, float] = (1.00, 5.00)  # Fallback for unknown models


class BudgetGuard:
    """Hard-cap cumulative token spend across a sweep.

    Shared across one or more agents via dependency injection. Each agent calls
    guard.charge() after every API call; if the cumulative cost exceeds max_usd,
    BudgetExceededError is raised immediately.

    Use pre_check() before making an API call to prevent exceeding the budget,
    and charge() after the call to record actual usage.

    Not thread-safe. For concurrent use, create separate instances per thread
    or protect with threading.Lock.
    """

    def __init__(self, max_usd: float) -> None:
        if max_usd <= 0:
            raise ValueError(f"max_usd must be positive, got {max_usd}")
        self._max_usd = max_usd
        self._spent_usd = 0.0
        self._call_count = 0

    def charge(self, input_tokens: int, output_tokens: int, model: str) -> None:
        """Record actual API usage. Raises BudgetExceededError if limit exceeded.

        Note: This is post-call detection. The API call has already completed.
        For pre-call prevention, use pre_check() before making the request.
        """
        in_price, out_price = _PRICES.get(model, _DEFAULT_PRICE)
        cost = (input_tokens * in_price + output_tokens * out_price) / 1_000_000
        self._spent_usd += cost
        self._call_count += 1
        if self._spent_usd > self._max_usd:
            raise BudgetExceededError(self._spent_usd, self._max_usd)

    def pre_check(self, max_tokens: int, model: str) -> None:
        """Pre-flight check: raise BudgetExceededError if worst-case cost would exceed budget.

        Call this BEFORE making the API request using max_tokens as pessimistic
        estimate. Uses max_tokens for both input and output as a conservative
        upper bound.
        """
        in_price, out_price = _PRICES.get(model, _DEFAULT_PRICE)
        worst_case_cost = (max_tokens * in_price + max_tokens * out_price) / 1_000_000
        if self._spent_usd + worst_case_cost > self._max_usd:
            raise BudgetExceededError(self._spent_usd + worst_case_cost, self._max_usd)

    @property
    def spent_usd(self) -> float:
        """Cumulative spend in USD."""
        return self._spent_usd

    @property
    def remaining_usd(self) -> float:
        """Remaining budget in USD (clamped to zero)."""
        return max(0.0, self._max_usd - self._spent_usd)

    @property
    def call_count(self) -> int:
        """Number of charge() calls made."""
        return self._call_count

    def reset(self) -> None:
        """Reset spend tracking (useful between sweeps)."""
        self._spent_usd = 0.0
        self._call_count = 0
