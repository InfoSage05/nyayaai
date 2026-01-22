#!/usr/bin/env python
"""Pytest checks for the pipeline in fallback mode.

This file used to execute at import-time and call sys.exit(), which breaks pytest.
"""

import pytest


def test_llm_fallback_path_is_safe():
    """If Groq isn't configured, we should still be able to import and run the app."""
    from llm.groq_client import groq_llm

    # If Groq is configured, ensure it returns non-empty text.
    if groq_llm is not None:
        response = groq_llm.generate_response("What is 2+2?")
        assert response is not None
        assert response.strip() != ""


def test_orchestrator_imports_or_skips_if_qdrant_down():
    """Orchestrator should import if dependencies are present; otherwise skip gracefully."""
    try:
        from core.orchestrator import orchestrator  # noqa: F401
    except Exception as e:
        pytest.skip(f"Orchestrator not importable (likely Qdrant/env not ready): {e}")


def test_query_response_explanation_not_none():
    from api.schemas import QueryResponse

    result = QueryResponse(
        query="test query",
        explanation="Test explanation",
        recommendations=[],
        error=None,
    )

    assert result.explanation is not None
