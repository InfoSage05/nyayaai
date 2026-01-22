#!/usr/bin/env python
"""Pytest checks for error-handling / fallback mode.

This used to be a script that executed at import-time and called sys.exit(),
which breaks pytest collection. Keep it as real tests so CI can run it.
"""

import pytest


def test_llm_import_does_not_crash():
    """Importing the LLM module should not hard-fail if 'groq' isn't installed."""
    from llm.groq_client import groq_llm  # noqa: F401


def test_reasoning_agent_import_does_not_crash():
    """ReasoningAgent should import even if groq_llm is unavailable (fallback path)."""
    from agents.reasoning_agent import ReasoningAgent

    _ = ReasoningAgent()


def test_query_response_explanation_not_none():
    """API schemas should allow building a valid response without None explanation."""
    from api.schemas import QueryResponse

    result = QueryResponse(
        query="test query",
        explanation="Test explanation",
        recommendations=[],
        error=None,
    )

    assert result.explanation is not None
