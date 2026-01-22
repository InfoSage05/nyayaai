#!/usr/bin/env python3
"""Simple import test to identify crash source."""
import sys
import traceback

print("Step-by-step import test...")
print("=" * 50)

steps = [
    ("1. Settings", "from config.settings import settings"),
    ("2. LLM module", "from llm import groq_llm"),
    ("3. Qdrant client", "from database.qdrant_client import qdrant_manager, QDRANT_AVAILABLE"),
    ("4. Agent base", "from core.agent_base import BaseAgent, AgentInput, AgentOutput"),
    ("5. Individual agents", """
from agents.intake_agent import IntakeAgent
from agents.classification_agent import ClassificationAgent
from agents.summarization_agent import SummarizationAgent
    """),
    ("6. Orchestrator class", "from core.orchestrator import NyayaOrchestrator"),
    ("7. FastAPI", "from api.main import app"),
    ("8. Streamlit", "from frontend.app import process_query"),
]

for step_name, import_code in steps:
    try:
        print(f"\n{step_name}...")
        exec(import_code)
        print(f"   ✓ {step_name} imported successfully")
    except Exception as e:
        print(f"   ✗ {step_name} failed: {e}")
        traceback.print_exc()
        print(f"\n❌ Crash occurred at: {step_name}")
        sys.exit(1)

print("\n" + "=" * 50)
print("✅ All imports successful - no crashes detected!")
print("\nNote: Orchestrator instance creation is deferred to prevent crashes.")
