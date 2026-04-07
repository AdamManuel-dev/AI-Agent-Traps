"""
Tests for AnthropicAgent -- SDK mocked throughout.

All tests mock the anthropic SDK so no real API calls are made.
Validates protocol conformance, process() behaviour, aprocess() async
behaviour, token tracking, budget integration, and error handling.
"""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_agent_traps.agents.budget_guard import BudgetExceededError, BudgetGuard

# -------------------------------------------------------------------------
# Helpers to mock the anthropic SDK
# -------------------------------------------------------------------------


def _make_mock_anthropic(
    response_text: str = "Hello!",
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> ModuleType:
    """Create a mock anthropic module with working Anthropic and AsyncAnthropic clients."""
    mock_module = ModuleType("anthropic")

    # Build mock response
    mock_content_block = MagicMock()
    mock_content_block.text = response_text

    mock_usage = MagicMock()
    mock_usage.input_tokens = input_tokens
    mock_usage.output_tokens = output_tokens

    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_response.usage = mock_usage

    # Build mock sync client
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    mock_anthropic_class = MagicMock(return_value=mock_client)
    mock_module.Anthropic = mock_anthropic_class  # type: ignore[attr-defined]

    # Build mock async client for aprocess()
    mock_async_client = MagicMock()
    mock_async_client.messages.create = AsyncMock(return_value=mock_response)

    mock_async_anthropic_class = MagicMock(return_value=mock_async_client)
    mock_module.AsyncAnthropic = mock_async_anthropic_class  # type: ignore[attr-defined]

    return mock_module


def _create_agent(
    mock_module: ModuleType,
    model: str = "claude-haiku-4-5-20251001",
    system_prompt: str | None = None,
    max_tokens: int = 512,
    budget_usd: float | None = None,
    budget_guard: BudgetGuard | None = None,
) -> object:
    """Create an AnthropicAgent with the mock anthropic module injected."""
    with patch.dict(sys.modules, {"anthropic": mock_module}):
        from ai_agent_traps.agents.anthropic_agent import AnthropicAgent

        return AnthropicAgent(
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            budget_usd=budget_usd,
            budget_guard=budget_guard,
        )


# -------------------------------------------------------------------------
# Protocol conformance
# -------------------------------------------------------------------------


class TestAnthropicAgentProtocol:
    """Verify AnthropicAgent satisfies AgentProtocol structurally."""

    def test_has_is_bot_attribute(self) -> None:
        from ai_agent_traps.agents.anthropic_agent import AnthropicAgent

        assert hasattr(AnthropicAgent, "is_bot")
        assert AnthropicAgent.is_bot is True

    def test_has_process_method(self) -> None:
        from ai_agent_traps.agents.anthropic_agent import AnthropicAgent

        assert hasattr(AnthropicAgent, "process")
        assert callable(AnthropicAgent.process)

    def test_satisfies_agent_protocol_at_runtime(self) -> None:
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module)

        from ai_agent_traps.agent import AgentProtocol

        assert isinstance(agent, AgentProtocol)


# -------------------------------------------------------------------------
# process() behaviour
# -------------------------------------------------------------------------


class TestAnthropicAgentProcess:
    """Validate process() calls the SDK correctly and returns text."""

    def test_process_returns_response_text(self) -> None:
        mock_module = _make_mock_anthropic(response_text="Mocked response")
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            result = agent.process("test input")  # type: ignore[union-attr]
        assert result == "Mocked response"

    def test_process_returns_string(self) -> None:
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            result = agent.process("hello")  # type: ignore[union-attr]
        assert isinstance(result, str)

    def test_process_passes_user_message(self) -> None:
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("specific input text")  # type: ignore[union-attr]
        mock_client = mock_module.Anthropic.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs.get("messages", call_kwargs[1].get("messages"))
        assert any("specific input text" in str(m) for m in messages)

    def test_process_passes_system_prompt_when_set(self) -> None:
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module, system_prompt="You are a test agent.")
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("hello")  # type: ignore[union-attr]
        mock_client = mock_module.Anthropic.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_client.messages.create.call_args
        # system prompt should be in kwargs
        assert "system" in call_kwargs.kwargs or "system" in call_kwargs[1]

    def test_process_omits_system_prompt_when_none(self) -> None:
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module, system_prompt=None)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("hello")  # type: ignore[union-attr]
        mock_client = mock_module.Anthropic.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_client.messages.create.call_args
        all_kwargs = {**call_kwargs.kwargs, **(call_kwargs[1] if len(call_kwargs) > 1 else {})}
        assert "system" not in all_kwargs


# -------------------------------------------------------------------------
# aprocess() async behaviour
# -------------------------------------------------------------------------


class TestAnthropicAgentAprocess:
    """Validate aprocess() uses AsyncAnthropic and returns text."""

    def test_aprocess_returns_string(self) -> None:
        """aprocess() returns the response text asynchronously."""
        mock_module = _make_mock_anthropic(response_text="Async mocked response")
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            result = asyncio.run(agent.aprocess("hello"))  # type: ignore[union-attr]
        assert result == "Async mocked response"
        assert isinstance(result, str)

    def test_aprocess_tracks_tokens(self) -> None:
        """aprocess() updates token counters like process()."""
        mock_module = _make_mock_anthropic(input_tokens=100, output_tokens=50)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            asyncio.run(agent.aprocess("test"))  # type: ignore[union-attr]
        assert agent.total_tokens_used == 150  # type: ignore[union-attr]

    def test_aprocess_uses_async_client(self) -> None:
        """aprocess() creates an AsyncAnthropic client, not the sync one."""
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            asyncio.run(agent.aprocess("hello"))  # type: ignore[union-attr]
        # AsyncAnthropic should have been called
        mock_module.AsyncAnthropic.assert_called_once()  # type: ignore[attr-defined]

    def test_aprocess_passes_system_prompt(self) -> None:
        """aprocess() includes system prompt in kwargs when set."""
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module, system_prompt="Be helpful.")
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            asyncio.run(agent.aprocess("hello"))  # type: ignore[union-attr]
        mock_async_client = mock_module.AsyncAnthropic.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_async_client.messages.create.call_args
        assert "system" in call_kwargs.kwargs or "system" in call_kwargs[1]

    def test_aprocess_charges_budget_guard(self) -> None:
        """aprocess() charges the budget guard after API call."""
        guard = BudgetGuard(max_usd=10.0)
        mock_module = _make_mock_anthropic(input_tokens=100, output_tokens=50)
        agent = _create_agent(mock_module, budget_guard=guard)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            asyncio.run(agent.aprocess("test"))  # type: ignore[union-attr]
        assert guard.spent_usd > 0.0


# -------------------------------------------------------------------------
# Token tracking
# -------------------------------------------------------------------------


class TestAnthropicAgentTokenTracking:
    """Validate token counting across process() calls."""

    def test_tokens_tracked_after_single_call(self) -> None:
        mock_module = _make_mock_anthropic(input_tokens=100, output_tokens=50)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert agent.total_tokens_used == 150  # type: ignore[union-attr]

    def test_tokens_accumulate_across_calls(self) -> None:
        mock_module = _make_mock_anthropic(input_tokens=10, output_tokens=5)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("call 1")  # type: ignore[union-attr]
            agent.process("call 2")  # type: ignore[union-attr]
        assert agent.total_tokens_used == 30  # type: ignore[union-attr]

    def test_total_cost_usd_is_positive(self) -> None:
        mock_module = _make_mock_anthropic(input_tokens=1000, output_tokens=500)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert agent.total_cost_usd > 0.0  # type: ignore[union-attr]


# -------------------------------------------------------------------------
# Budget guard integration
# -------------------------------------------------------------------------


class TestAnthropicAgentBudget:
    """Validate BudgetGuard integration."""

    def test_budget_guard_shared_instance(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        mock_module = _make_mock_anthropic(input_tokens=100, output_tokens=50)
        agent = _create_agent(mock_module, budget_guard=guard)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert guard.spent_usd > 0.0

    def test_budget_usd_creates_internal_guard(self) -> None:
        mock_module = _make_mock_anthropic(input_tokens=100, output_tokens=50)
        agent = _create_agent(mock_module, budget_usd=10.0)
        with patch.dict(sys.modules, {"anthropic": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        # Should not raise -- budget is large enough
        assert agent.total_tokens_used == 150  # type: ignore[union-attr]

    def test_budget_exceeded_raises(self) -> None:
        guard = BudgetGuard(max_usd=0.0001)
        mock_module = _make_mock_anthropic(input_tokens=1_000_000, output_tokens=1_000_000)
        agent = _create_agent(mock_module, budget_guard=guard)
        with pytest.raises(BudgetExceededError):
            with patch.dict(sys.modules, {"anthropic": mock_module}):
                agent.process("expensive call")  # type: ignore[union-attr]


# -------------------------------------------------------------------------
# Import error handling
# -------------------------------------------------------------------------


class TestAnthropicAgentImportError:
    """Validate error when anthropic SDK is not installed."""

    def test_raises_import_error_without_sdk(self) -> None:
        # Temporarily remove anthropic from sys.modules
        with patch.dict(sys.modules, {"anthropic": None}):
            with pytest.raises(ImportError, match="anthropic SDK is required"):
                from ai_agent_traps.agents.anthropic_agent import AnthropicAgent

                AnthropicAgent()


# -------------------------------------------------------------------------
# Error path tests (M-6)
# -------------------------------------------------------------------------


class TestAnthropicAgentErrorPaths:
    """Validate that SDK exceptions propagate to caller."""

    def test_api_error_propagates(self) -> None:
        """SDK exception during process() should propagate to caller."""
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module)
        # Make messages.create raise an exception
        mock_client = mock_module.Anthropic.return_value  # type: ignore[attr-defined]
        mock_client.messages.create.side_effect = Exception("API error")
        with pytest.raises(Exception, match="API error"):
            with patch.dict(sys.modules, {"anthropic": mock_module}):
                agent.process("test")  # type: ignore[union-attr]

    def test_empty_content_list_raises(self) -> None:
        """Empty response.content list should raise IndexError."""
        mock_module = _make_mock_anthropic()
        agent = _create_agent(mock_module)
        # Override response to have empty content list
        mock_client = mock_module.Anthropic.return_value  # type: ignore[attr-defined]
        mock_response = mock_client.messages.create.return_value
        mock_response.content = []
        with pytest.raises(IndexError):
            with patch.dict(sys.modules, {"anthropic": mock_module}):
                agent.process("test")  # type: ignore[union-attr]
