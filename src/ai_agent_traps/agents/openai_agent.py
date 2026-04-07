"""
OpenAI agent adapter using the OpenAI SDK.

Satisfies AgentProtocol (is_bot: bool, process(str) -> str) so it can be used
as a drop-in replacement for mock agents in evaluation sweeps.

The SDK is validated at construction time for fail-fast ImportError; the client
is initialized once and reused across process() calls.
Install with: pip install 'ai-agent-traps[llm]'
"""

from __future__ import annotations

from typing import Any

from ai_agent_traps.agents.budget_guard import BudgetGuard


class OpenAIAgent:
    """OpenAI chat completion agent satisfying AgentProtocol.

    Uses the OpenAI Chat Completions API. The SDK is validated at construction
    time for fail-fast ImportError; the client is created once in __init__ and
    reused across all process() calls.

    Not thread-safe. For concurrent use, create separate instances per thread
    or protect with threading.Lock.
    """

    is_bot: bool = True

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        system_prompt: str | None = None,
        max_tokens: int = 512,
        budget_usd: float | None = None,
        budget_guard: BudgetGuard | None = None,
    ) -> None:
        try:
            import openai
        except ImportError as exc:
            raise ImportError(
                "openai SDK is required. "
                "Install with: pip install 'ai-agent-traps[llm]'"
            ) from exc

        self._model = model
        self._system_prompt = system_prompt
        self._max_tokens = max_tokens
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._client = openai.OpenAI()
        # Lazy-initialized in aprocess(); typed as Any because the
        # openai.AsyncOpenAI type is only available at runtime.
        self._async_client: Any = None

        if budget_guard is not None:
            self._budget_guard: BudgetGuard | None = budget_guard
        elif budget_usd is not None:
            self._budget_guard = BudgetGuard(budget_usd)
        else:
            self._budget_guard = None

    def process(self, input_text: str) -> str:
        """Send input_text to OpenAI and return response text.

        SDK exceptions (e.g., openai.APIError) propagate to caller.
        For sweep usage, wrap in try/except or use the async runner's
        retry logic.
        """
        messages: list[dict[str, str]] = []
        if self._system_prompt is not None:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": input_text})

        response: Any = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=messages,  # type: ignore[arg-type]
        )

        usage = response.usage
        if usage is not None:
            self._total_input_tokens += usage.prompt_tokens
            self._total_output_tokens += usage.completion_tokens
            if self._budget_guard is not None:
                self._budget_guard.charge(
                    usage.prompt_tokens, usage.completion_tokens, self._model
                )

        content: str | None = response.choices[0].message.content
        return content or ""

    async def aprocess(self, input_text: str) -> str:
        """Async version of process(). Uses openai's async client.

        The AsyncOpenAI client is created lazily on first call and
        reused across subsequent calls. SDK exceptions propagate to caller.

        Not thread-safe. Designed for single-threaded asyncio event loops.
        """
        import openai

        if self._async_client is None:
            self._async_client = openai.AsyncOpenAI()

        messages: list[dict[str, str]] = []
        if self._system_prompt is not None:
            messages.append({"role": "system", "content": self._system_prompt})
        messages.append({"role": "user", "content": input_text})

        response = await self._async_client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=messages,
        )

        usage = response.usage
        if usage is not None:
            self._total_input_tokens += usage.prompt_tokens
            self._total_output_tokens += usage.completion_tokens
            if self._budget_guard is not None:
                self._budget_guard.charge(
                    usage.prompt_tokens, usage.completion_tokens, self._model
                )

        content: str | None = response.choices[0].message.content
        return content or ""

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
