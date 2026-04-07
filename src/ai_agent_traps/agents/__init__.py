"""
LLM agent adapters for AI Agent Traps evaluation.

Provides AnthropicAgent (Claude) and OpenAIAgent (GPT) adapters that satisfy
AgentProtocol, plus BudgetGuard for hard-cap spend protection during sweeps.

[UNSPECIFIED] The paper does not specify which LLM backends to use for
evaluation. These adapters enable testing the taxonomy against real LLMs.
"""

from ai_agent_traps.agents.anthropic_agent import AnthropicAgent
from ai_agent_traps.agents.budget_guard import BudgetExceededError, BudgetGuard
from ai_agent_traps.agents.openai_agent import OpenAIAgent

__all__ = ["AnthropicAgent", "BudgetExceededError", "BudgetGuard", "OpenAIAgent"]
