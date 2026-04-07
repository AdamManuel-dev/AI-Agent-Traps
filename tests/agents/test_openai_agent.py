"""
Tests for OpenAIAgent -- SDK mocked throughout.

All tests mock the openai SDK so no real API calls are made.
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
# Helpers to mock the openai SDK
# -------------------------------------------------------------------------


def _make_mock_openai(
    response_text: str = "Hello!",
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    usage_present: bool = True,
) -> ModuleType:
    """Create a mock openai module with working OpenAI and AsyncOpenAI clients."""
    mock_module = ModuleType("openai")

    # Build mock response
    mock_message = MagicMock()
    mock_message.content = response_text

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage if usage_present else None

    # Build mock sync client
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    mock_openai_class = MagicMock(return_value=mock_client)
    mock_module.OpenAI = mock_openai_class  # type: ignore[attr-defined]

    # Build mock async client for aprocess()
    mock_async_client = MagicMock()
    mock_async_client.chat.completions.create = AsyncMock(return_value=mock_response)

    mock_async_openai_class = MagicMock(return_value=mock_async_client)
    mock_module.AsyncOpenAI = mock_async_openai_class  # type: ignore[attr-defined]

    return mock_module


def _create_agent(
    mock_module: ModuleType,
    model: str = "gpt-4o-mini",
    system_prompt: str | None = None,
    max_tokens: int = 512,
    budget_usd: float | None = None,
    budget_guard: BudgetGuard | None = None,
) -> object:
    """Create an OpenAIAgent with the mock openai module injected."""
    with patch.dict(sys.modules, {"openai": mock_module}):
        from ai_agent_traps.agents.openai_agent import OpenAIAgent

        return OpenAIAgent(
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            budget_usd=budget_usd,
            budget_guard=budget_guard,
        )


# -------------------------------------------------------------------------
# Protocol conformance
# -------------------------------------------------------------------------


class TestOpenAIAgentProtocol:
    """Verify OpenAIAgent satisfies AgentProtocol structurally."""

    def test_has_is_bot_attribute(self) -> None:
        from ai_agent_traps.agents.openai_agent import OpenAIAgent

        assert hasattr(OpenAIAgent, "is_bot")
        assert OpenAIAgent.is_bot is True

    def test_has_process_method(self) -> None:
        from ai_agent_traps.agents.openai_agent import OpenAIAgent

        assert hasattr(OpenAIAgent, "process")
        assert callable(OpenAIAgent.process)

    def test_satisfies_agent_protocol_at_runtime(self) -> None:
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module)

        from ai_agent_traps.agent import AgentProtocol

        assert isinstance(agent, AgentProtocol)


# -------------------------------------------------------------------------
# process() behaviour
# -------------------------------------------------------------------------


class TestOpenAIAgentProcess:
    """Validate process() calls the SDK correctly and returns text."""

    def test_process_returns_response_text(self) -> None:
        mock_module = _make_mock_openai(response_text="Mocked GPT response")
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            result = agent.process("test input")  # type: ignore[union-attr]
        assert result == "Mocked GPT response"

    def test_process_returns_string(self) -> None:
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            result = agent.process("hello")  # type: ignore[union-attr]
        assert isinstance(result, str)

    def test_process_passes_user_message(self) -> None:
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("specific input text")  # type: ignore[union-attr]
        mock_client = mock_module.OpenAI.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages", call_kwargs[1].get("messages"))
        assert any("specific input text" in str(m) for m in messages)

    def test_process_includes_system_prompt_when_set(self) -> None:
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module, system_prompt="You are a test agent.")
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("hello")  # type: ignore[union-attr]
        mock_client = mock_module.OpenAI.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages", call_kwargs[1].get("messages"))
        # system message should be first in the list
        assert any("system" in str(m) for m in messages)

    def test_process_omits_system_prompt_when_none(self) -> None:
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module, system_prompt=None)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("hello")  # type: ignore[union-attr]
        mock_client = mock_module.OpenAI.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages", call_kwargs[1].get("messages"))
        # Only user message should be present
        assert len(messages) == 1

    def test_process_handles_none_content(self) -> None:
        """When the model returns None content, process() should return empty string."""
        mock_module = _make_mock_openai(response_text="placeholder")
        # Overwrite the content to None
        mock_client = mock_module.OpenAI.return_value  # type: ignore[attr-defined]
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices[0].message.content = None

        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            result = agent.process("test")  # type: ignore[union-attr]
        assert result == ""


# -------------------------------------------------------------------------
# aprocess() async behaviour
# -------------------------------------------------------------------------


class TestOpenAIAgentAprocess:
    """Validate aprocess() uses AsyncOpenAI and returns text."""

    def test_aprocess_returns_string(self) -> None:
        """aprocess() returns the response text asynchronously."""
        mock_module = _make_mock_openai(response_text="Async GPT response")
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            result = asyncio.run(agent.aprocess("hello"))  # type: ignore[union-attr]
        assert result == "Async GPT response"
        assert isinstance(result, str)

    def test_aprocess_tracks_tokens(self) -> None:
        """aprocess() updates token counters like process()."""
        mock_module = _make_mock_openai(prompt_tokens=100, completion_tokens=50)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            asyncio.run(agent.aprocess("test"))  # type: ignore[union-attr]
        assert agent.total_tokens_used == 150  # type: ignore[union-attr]

    def test_aprocess_uses_async_client(self) -> None:
        """aprocess() creates an AsyncOpenAI client, not the sync one."""
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            asyncio.run(agent.aprocess("hello"))  # type: ignore[union-attr]
        # AsyncOpenAI should have been called
        mock_module.AsyncOpenAI.assert_called_once()  # type: ignore[attr-defined]

    def test_aprocess_includes_system_prompt(self) -> None:
        """aprocess() includes system prompt in messages when set."""
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module, system_prompt="Be helpful.")
        with patch.dict(sys.modules, {"openai": mock_module}):
            asyncio.run(agent.aprocess("hello"))  # type: ignore[union-attr]
        mock_async_client = mock_module.AsyncOpenAI.return_value  # type: ignore[attr-defined]
        call_kwargs = mock_async_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages", call_kwargs[1].get("messages"))
        assert any("system" in str(m) for m in messages)

    def test_aprocess_charges_budget_guard(self) -> None:
        """aprocess() charges the budget guard after API call."""
        guard = BudgetGuard(max_usd=10.0)
        mock_module = _make_mock_openai(prompt_tokens=100, completion_tokens=50)
        agent = _create_agent(mock_module, budget_guard=guard)
        with patch.dict(sys.modules, {"openai": mock_module}):
            asyncio.run(agent.aprocess("test"))  # type: ignore[union-attr]
        assert guard.spent_usd > 0.0

    def test_aprocess_handles_none_usage(self) -> None:
        """aprocess() gracefully handles None usage from API."""
        mock_module = _make_mock_openai(usage_present=False)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            result = asyncio.run(agent.aprocess("test"))  # type: ignore[union-attr]
        assert isinstance(result, str)
        assert agent.total_tokens_used == 0  # type: ignore[union-attr]


# -------------------------------------------------------------------------
# Token tracking
# -------------------------------------------------------------------------


class TestOpenAIAgentTokenTracking:
    """Validate token counting across process() calls."""

    def test_tokens_tracked_after_single_call(self) -> None:
        mock_module = _make_mock_openai(prompt_tokens=100, completion_tokens=50)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert agent.total_tokens_used == 150  # type: ignore[union-attr]

    def test_tokens_accumulate_across_calls(self) -> None:
        mock_module = _make_mock_openai(prompt_tokens=10, completion_tokens=5)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("call 1")  # type: ignore[union-attr]
            agent.process("call 2")  # type: ignore[union-attr]
        assert agent.total_tokens_used == 30  # type: ignore[union-attr]

    def test_tokens_not_tracked_when_usage_is_none(self) -> None:
        mock_module = _make_mock_openai(usage_present=False)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert agent.total_tokens_used == 0  # type: ignore[union-attr]

    def test_total_cost_usd_is_positive(self) -> None:
        mock_module = _make_mock_openai(prompt_tokens=1000, completion_tokens=500)
        agent = _create_agent(mock_module)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert agent.total_cost_usd > 0.0  # type: ignore[union-attr]


# -------------------------------------------------------------------------
# Budget guard integration
# -------------------------------------------------------------------------


class TestOpenAIAgentBudget:
    """Validate BudgetGuard integration."""

    def test_budget_guard_shared_instance(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        mock_module = _make_mock_openai(prompt_tokens=100, completion_tokens=50)
        agent = _create_agent(mock_module, budget_guard=guard)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert guard.spent_usd > 0.0

    def test_budget_usd_creates_internal_guard(self) -> None:
        mock_module = _make_mock_openai(prompt_tokens=100, completion_tokens=50)
        agent = _create_agent(mock_module, budget_usd=10.0)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert agent.total_tokens_used == 150  # type: ignore[union-attr]

    def test_budget_exceeded_raises(self) -> None:
        guard = BudgetGuard(max_usd=0.0001)
        mock_module = _make_mock_openai(prompt_tokens=1_000_000, completion_tokens=1_000_000)
        agent = _create_agent(mock_module, budget_guard=guard)
        with pytest.raises(BudgetExceededError):
            with patch.dict(sys.modules, {"openai": mock_module}):
                agent.process("expensive call")  # type: ignore[union-attr]

    def test_no_budget_tracking_when_usage_none(self) -> None:
        guard = BudgetGuard(max_usd=10.0)
        mock_module = _make_mock_openai(usage_present=False)
        agent = _create_agent(mock_module, budget_guard=guard)
        with patch.dict(sys.modules, {"openai": mock_module}):
            agent.process("test")  # type: ignore[union-attr]
        assert guard.spent_usd == 0.0


# -------------------------------------------------------------------------
# Import error handling
# -------------------------------------------------------------------------


class TestOpenAIAgentImportError:
    """Validate error when openai SDK is not installed."""

    def test_raises_import_error_without_sdk(self) -> None:
        with patch.dict(sys.modules, {"openai": None}):
            with pytest.raises(ImportError, match="openai SDK is required"):
                from ai_agent_traps.agents.openai_agent import OpenAIAgent

                OpenAIAgent()


# -------------------------------------------------------------------------
# Error path tests (M-6)
# -------------------------------------------------------------------------


class TestOpenAIAgentErrorPaths:
    """Validate that SDK exceptions propagate to caller."""

    def test_api_error_propagates(self) -> None:
        """SDK exception during process() should propagate to caller."""
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module)
        # Make chat.completions.create raise an exception
        mock_client = mock_module.OpenAI.return_value  # type: ignore[attr-defined]
        mock_client.chat.completions.create.side_effect = Exception("API error")
        with pytest.raises(Exception, match="API error"):
            with patch.dict(sys.modules, {"openai": mock_module}):
                agent.process("test")  # type: ignore[union-attr]

    def test_empty_choices_list_raises(self) -> None:
        """Empty response.choices list should raise IndexError."""
        mock_module = _make_mock_openai()
        agent = _create_agent(mock_module)
        # Override response to have empty choices list
        mock_client = mock_module.OpenAI.return_value  # type: ignore[attr-defined]
        mock_response = mock_client.chat.completions.create.return_value
        mock_response.choices = []
        with pytest.raises(IndexError):
            with patch.dict(sys.modules, {"openai": mock_module}):
                agent.process("test")  # type: ignore[union-attr]
