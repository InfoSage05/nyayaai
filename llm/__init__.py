"""LLM module initialization."""
import logging

# Configure logging for LLM module
logger = logging.getLogger(__name__)

try:
    from llm.groq_client import groq_llm, GroqLLM
    __all__ = ["groq_llm", "GroqLLM", "logger"]
except (ImportError, ValueError) as e:
    # Fallback if groq_client can't be imported or initialized
    logger.warning(f"LLM module initialization warning: {e}")
    groq_llm = None
    try:
        from llm.groq_client import GroqLLM
    except ImportError:
        GroqLLM = None
    __all__ = ["groq_llm", "GroqLLM", "logger"]
