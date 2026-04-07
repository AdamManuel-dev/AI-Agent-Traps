"""
Tests for ai_agent_traps.agents.budget_guard -- spend protection.

Validates BudgetGuard tracking, BudgetExceededError, pricing lookup,
edge cases, pre_check(), and reset behaviour.
"""

from __future__ import annotations

import pytest

from ai_agent_traps.agents.budget_guard import (
    _DEFAULT_PRICE,
    _PRICES,
    BudgetExceededError,
    BudgetGuard,
)

# -------------------------------------------------------------------------
# BudgetGuard construction
# -------------------------------------------------------------------------


class TestBudgetGuardInit:
    """Validate BudgetGuard construction and initial state."""

    def test_initial_spent_is_zero(self) -> None:
        guard = BudgetGuard(max_usd=1.0)
        assert guard.spent_usd == 0.0

    def test_initial_remaining_equals_max(self) -> None:
        guard = BudgetGuard(max_usd=5.0)
        assert guard.remaining_usd == 5.0

    def test_initial_call_count_is_zero(self) -> None:
        guard = BudgetGuard(max_usd=1.0)
        assert guard.call_count == 0

    def test_rejects_zero_budget(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            BudgetGuard(max_usd=0.0)

    def test_rejects_negative_budget(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            BudgetGuard(max_usd=-1.0)

    def test_accepts_small_budget(self) -> None:
        guard = BudgetGuard(max_usd=0.001)
        assert guard.remaining_usd == 0.001


# -------------------------------------------------------------------------
# BudgetGuard.charge()
# -------------------------------------------------------------------------


class TestBudgetGuardCharge:
    """Validate charge tracking and budget enforcement."""

    def test_charge_increases_spent(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(1000, 500, "claude-haiku-4-5-20251001")
        assert guard.spent_usd > 0.0

    def test_charge_decreases_remaining(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(1000, 500, "claude-haiku-4-5-20251001")
        assert guard.remaining_usd < 10.0

    def test_charge_increments_call_count(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(100, 50, "gpt-4o-mini")
        guard.charge(100, 50, "gpt-4o-mini")
        assert guard.call_count == 2

    def test_charge_accumulates_across_calls(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(1000, 500, "gpt-4o-mini")
        first_spent = guard.spent_usd
        guard.charge(1000, 500, "gpt-4o-mini")
        assert guard.spent_usd > first_spent

    def test_charge_raises_on_budget_exceeded(self) -> None:
        guard = BudgetGuard(max_usd=0.001)
        with pytest.raises(BudgetExceededError):
            guard.charge(1_000_000, 1_000_000, "claude-haiku-4-5-20251001")

    def test_charge_uses_correct_model_pricing(self) -> None:
        guard = BudgetGuard(max_usd=100.0)
        # claude-haiku: input=0.80/1M, output=4.00/1M
        guard.charge(1_000_000, 0, "claude-haiku-4-5-20251001")
        assert abs(guard.spent_usd - 0.80) < 0.001

    def test_charge_uses_default_price_for_unknown_model(self) -> None:
        guard = BudgetGuard(max_usd=100.0)
        # default: input=1.00/1M, output=5.00/1M
        guard.charge(1_000_000, 0, "unknown-model-v99")
        assert abs(guard.spent_usd - _DEFAULT_PRICE[0]) < 0.001

    def test_zero_tokens_costs_nothing(self) -> None:
        guard = BudgetGuard(max_usd=1.0)
        guard.charge(0, 0, "gpt-4o")
        assert guard.spent_usd == 0.0
        assert guard.call_count == 1

    def test_remaining_clamps_to_zero(self) -> None:
        guard = BudgetGuard(max_usd=0.01)
        try:
            guard.charge(1_000_000, 1_000_000, "claude-opus-4-6")
        except BudgetExceededError:
            pass
        assert guard.remaining_usd == 0.0


# -------------------------------------------------------------------------
# BudgetGuard.pre_check()
# -------------------------------------------------------------------------


class TestBudgetGuardPreCheck:
    """Validate pre-flight budget check before API calls."""

    def test_pre_check_passes_when_within_budget(self) -> None:
        guard = BudgetGuard(max_usd=100.0)
        # Should not raise for small max_tokens with large budget
        guard.pre_check(512, "claude-haiku-4-5-20251001")

    def test_pre_check_raises_when_would_exceed_budget(self) -> None:
        guard = BudgetGuard(max_usd=0.001)
        with pytest.raises(BudgetExceededError):
            # 1M tokens * (0.80 + 4.00) / 1M = $4.80 >> $0.001
            guard.pre_check(1_000_000, "claude-haiku-4-5-20251001")

    def test_pre_check_considers_existing_spend(self) -> None:
        guard = BudgetGuard(max_usd=1.0)
        # Spend most of the budget
        guard.charge(1_000_000, 0, "claude-haiku-4-5-20251001")  # $0.80
        # Pre-check should raise because worst-case additional $4.80 > remaining $0.20
        with pytest.raises(BudgetExceededError):
            guard.pre_check(1_000_000, "claude-haiku-4-5-20251001")

    def test_pre_check_does_not_modify_spent(self) -> None:
        guard = BudgetGuard(max_usd=100.0)
        guard.pre_check(512, "gpt-4o-mini")
        assert guard.spent_usd == 0.0
        assert guard.call_count == 0

    def test_pre_check_uses_default_price_for_unknown_model(self) -> None:
        guard = BudgetGuard(max_usd=0.001)
        with pytest.raises(BudgetExceededError):
            guard.pre_check(1_000_000, "unknown-model-v99")

    def test_pre_check_uses_worst_case_both_directions(self) -> None:
        """pre_check uses max_tokens for both input and output (conservative)."""
        guard = BudgetGuard(max_usd=100.0)
        # gpt-4o-mini: input=0.15/1M, output=0.60/1M
        # worst_case = 1M * (0.15 + 0.60) / 1M = $0.75
        guard.pre_check(1_000_000, "gpt-4o-mini")
        # Should pass since $0.75 < $100.0

        tiny_guard = BudgetGuard(max_usd=0.50)
        with pytest.raises(BudgetExceededError):
            # worst_case = 1M * (0.15 + 0.60) / 1M = $0.75 > $0.50
            tiny_guard.pre_check(1_000_000, "gpt-4o-mini")


# -------------------------------------------------------------------------
# BudgetGuard.reset()
# -------------------------------------------------------------------------


class TestBudgetGuardReset:
    """Validate reset clears tracking state."""

    def test_reset_clears_spent(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(10000, 5000, "gpt-4o-mini")
        guard.reset()
        assert guard.spent_usd == 0.0

    def test_reset_restores_remaining(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(10000, 5000, "gpt-4o-mini")
        guard.reset()
        assert guard.remaining_usd == 10.0

    def test_reset_clears_call_count(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        guard.charge(100, 50, "gpt-4o-mini")
        guard.reset()
        assert guard.call_count == 0


# -------------------------------------------------------------------------
# BudgetExceededError
# -------------------------------------------------------------------------


class TestBudgetExceededError:
    """Validate error attributes and message."""

    def test_error_message_contains_amounts(self) -> None:
        err = BudgetExceededError(spent=1.5, limit=1.0)
        assert "1.5" in str(err)
        assert "1.0" in str(err)

    def test_error_attributes(self) -> None:
        err = BudgetExceededError(spent=2.0, limit=1.0)
        assert err.spent == 2.0
        assert err.limit == 1.0

    def test_error_is_exception(self) -> None:
        assert issubclass(BudgetExceededError, Exception)


# -------------------------------------------------------------------------
# Pricing table
# -------------------------------------------------------------------------


class TestPricingTable:
    """Validate pricing constants are reasonable."""

    def test_all_prices_are_positive(self) -> None:
        for model, (in_p, out_p) in _PRICES.items():
            assert in_p > 0, f"{model} input price not positive"
            assert out_p > 0, f"{model} output price not positive"

    def test_default_price_is_positive(self) -> None:
        assert _DEFAULT_PRICE[0] > 0
        assert _DEFAULT_PRICE[1] > 0

    def test_output_price_gte_input_price(self) -> None:
        """Output tokens are typically more expensive than input tokens."""
        for model, (in_p, out_p) in _PRICES.items():
            assert out_p >= in_p, f"{model} output price < input price"

    def test_known_models_present(self) -> None:
        assert "claude-haiku-4-5-20251001" in _PRICES
        assert "gpt-4o-mini" in _PRICES
        assert "gpt-4o" in _PRICES
