#!/usr/bin/env python3
"""Test script to check for import and syntax errors."""
import sys
import traceback

print("Testing imports and basic syntax...")
print("=" * 50)

errors = []

# Test 1: Frontend app
try:
    print("1. Testing frontend/app.py...")
    from frontend.app import process_query, display_results, main
    print("   ✓ frontend/app.py imports successfully")
except Exception as e:
    print(f"   ✗ Error in frontend/app.py: {e}")
    errors.append(("frontend/app.py", e))
    traceback.print_exc()

# Test 2: API main
try:
    print("\n2. Testing api/main.py...")
    from api.main import app
    print("   ✓ api/main.py imports successfully")
except Exception as e:
    print(f"   ✗ Error in api/main.py: {e}")
    errors.append(("api/main.py", e))
    traceback.print_exc()

# Test 3: Orchestrator
try:
    print("\n3. Testing core/orchestrator.py...")
    from core.orchestrator import NyayaOrchestrator
    print("   ✓ core/orchestrator.py imports successfully")
except Exception as e:
    print(f"   ✗ Error in core/orchestrator.py: {e}")
    errors.append(("core/orchestrator.py", e))
    traceback.print_exc()

# Test 4: All agents
try:
    print("\n4. Testing all agents...")
    from agents.summarization_agent import SummarizationAgent
    from agents.classification_agent import ClassificationAgent
    from agents.recommendation_agent import RecommendationAgent
    from agents.case_similarity_agent import CaseSimilarityAgent
    from agents.ethics_agent import EthicsAgent
    print("   ✓ All agents import successfully")
except Exception as e:
    print(f"   ✗ Error importing agents: {e}")
    errors.append(("agents", e))
    traceback.print_exc()

# Test 5: LLM module
try:
    print("\n5. Testing llm module...")
    from llm import groq_llm
    print(f"   ✓ llm module imports successfully (groq_llm: {groq_llm is not None})")
except Exception as e:
    print(f"   ✗ Error in llm module: {e}")
    errors.append(("llm", e))
    traceback.print_exc()

print("\n" + "=" * 50)
if errors:
    print(f"❌ Found {len(errors)} error(s):")
    for file, error in errors:
        print(f"   - {file}: {error}")
    sys.exit(1)
else:
    print("✅ All imports successful! Code is ready to run.")
    sys.exit(0)
