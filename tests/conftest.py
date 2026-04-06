"""
Shared pytest fixtures for the AI Agent Traps test suite.

Provides pre-instantiated mock agents for use across all test modules.
"""

from __future__ import annotations

import pytest

from ai_agent_traps.agent import EchoAgent, FilteredAgent, MemoryAgent, NaiveAgent


@pytest.fixture
def echo_agent() -> EchoAgent:
    return EchoAgent()


@pytest.fixture
def naive_agent() -> NaiveAgent:
    return NaiveAgent()


@pytest.fixture
def filtered_agent() -> FilteredAgent:
    return FilteredAgent()


@pytest.fixture
def memory_agent() -> MemoryAgent:
    return MemoryAgent()
