"""
AI Agent Traps -- Pluggable Success Metrics

Exports the SuccessMetric protocol and concrete implementations.
Pass any SuccessMetric to run_single_eval(metric=...) to override the
default keyword overlap heuristic.
"""

from ai_agent_traps.metrics.base import SuccessMetric
from ai_agent_traps.metrics.keyword_overlap import KeywordOverlapMetric
from ai_agent_traps.metrics.llm_judge import LLMJudgeMetric

# SemanticSimilarityMetric requires [rag] extra (sentence-transformers).
# Import raises ImportError at *instantiation* time, not import time, so
# re-exporting the class is safe -- users only get an error when they call
# SemanticSimilarityMetric().
from ai_agent_traps.metrics.semantic_similarity import SemanticSimilarityMetric

__all__ = [
    "KeywordOverlapMetric",
    "LLMJudgeMetric",
    "SemanticSimilarityMetric",
    "SuccessMetric",
]
