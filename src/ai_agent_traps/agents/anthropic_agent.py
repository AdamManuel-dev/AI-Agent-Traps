"""
Claude agent adapter using the Anthropic SDK.

Satisfies AgentProtocol (is_bot: bool, process(str) -> str) so it can be used
as a drop-in replacement for mock agents in evaluation sweeps.

The SDK is validated at construction time for fail-fast ImportError; the client
is initialized once and reused across process() calls.
Install with: pip install 'ai-agent-traps[llm]'
"""

from __future__ import annotations

from typing import Any

from ai_agent_traps.agents.budget_guard import BudgetGuard


class AnthropicAgent:
    """Claude agent satisfying AgentProtocol.

    Uses the Anthropic Messages API. The SDK is validated at construction time
    for fail-fast ImportError; the client is created once in __init__ and
    reused across all process() calls.

    Not thread-safe. For concurrent use, create separate instances per thread
    or protect with threading.Lock.
    """

    is_bot: bool = True

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        system_prompt: str | None = None,
        max_tokens: int = 512,
        budget_usd: float | None = None,
        budget_guard: BudgetGuard | None = None,
    ) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "anthropic SDK is required. "
                "Install with: pip install 'ai-agent-traps[llm]'"
            ) from exc

        self._model = model
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._client = anthropic.Anthropic()
        # Lazy-initialized in aprocess(); typed as Any because the
        # anthropic.AsyncAnthropic type is only available at runtime.
        self._async_client: Any = None

        if budget_guard is not None:
            self._budget_guard: BudgetGuard | None = budget_guard
        elif budget_usd is not None:
            self._budget_guard = BudgetGuard(budget_usd)
        else:
            self._budget_guard = None

    def process(self, input_text: str) -> str:
        """Send input_text to Claude and return response text.

        SDK exceptions (e.g., anthropic.APIError) propagate to caller.
        For sweep usage, wrap in try/except or use the async runner's
        retry logic.
        """
        messages: list[dict[str, str]] = [{"role": "user", "content": input_text}]

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }
        if self._system_prompt is not None:
            kwargs["system"] = self._system_prompt

        response = self._client.messages.create(**kwargs)

        usage = response.usage
        self._total_input_tokens += usage.input_tokens
        self._total_output_tokens += usage.output_tokens
        if self._budget_guard is not None:
            self._budget_guard.charge(
                usage.input_tokens, usage.output_tokens, self._model
            )

        # Extract text from the first content block (TextBlock).
        # response.content[0] is a union type; we access .text which is
        # present on TextBlock but not all block types.
        text: str = getattr(response.content[0], "text", "")
        return text

    async def aprocess(self, input_text: str) -> str:
        """Async version of process(). Uses anthropic's async client.

        The AsyncAnthropic client is created lazily on first call and
        reused across subsequent calls. SDK exceptions propagate to caller.

        Not thread-safe. Designed for single-threaded asyncio event loops.
        """
        import anthropic

        if self._async_client is None:
            self._async_client = anthropic.AsyncAnthropic()

        messages: list[dict[str, str]] = [{"role": "user", "content": input_text}]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }
        if self._system_prompt is not None:
            kwargs["system"] = self._system_prompt

        response = await self._async_client.messages.create(**kwargs)

        usage = response.usage
        self._total_input_tokens += usage.input_tokens
        self._total_output_tokens += usage.output_tokens
        if self._budget_guard is not None:
            self._budget_guard.charge(
                usage.input_tokens, usage.output_tokens, self._model
            )

        return getattr(response.content[0], "text", "")

    @property
    def total_tokens_used(self) -> int:
        """Total input + output tokens consumed across all calls."""
        return self._total_input_tokens + self._total_output_tokens

    @property
    def total_cost_usd(self) -> float:
        """Approximate cumulative cost in USD based on token usage."""
        from ai_agent_traps.agents.budget_guard import _DEFAULT_PRICE, _PRICES

        in_price, out_price = _PRICES.get(self._model, _DEFAULT_PRICE)
        return (
            self._total_input_tokens * in_price
            + self._total_output_tokens * out_price
        ) / 1_000_000
