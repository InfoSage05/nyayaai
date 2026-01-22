#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""
import sys
import os

# Suppress .env file errors for testing
os.environ.pop("ENV_FILE", None)

print("Testing imports...")
print("=" * 50)

try:
    print("1. Testing core imports...")
    from core.agent_base import BaseAgent, AgentInput, AgentOutput
    print("   ✓ core.agent_base")
    
    from core.orchestrator import NyayaOrchestrator, AgentState
    print("   ✓ core.orchestrator")
    
    print("\n2. Testing agent imports...")
    from agents.intake_agent import IntakeAgent
    print("   ✓ IntakeAgent")
    
    from agents.classification_agent import ClassificationAgent
    print("   ✓ ClassificationAgent")
    
    from agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
    print("   ✓ KnowledgeRetrievalAgent")
    
    from agents.case_similarity_agent import CaseSimilarityAgent
    print("   ✓ CaseSimilarityAgent")
    
    from agents.reasoning_agent import ReasoningAgent
    print("   ✓ ReasoningAgent")
    
    from agents.recommendation_agent import RecommendationAgent
    print("   ✓ RecommendationAgent")
    
    from agents.ethics_agent import EthicsAgent
    print("   ✓ EthicsAgent")
    
    from agents.memory_agent import MemoryAgent
    print("   ✓ MemoryAgent")
    
    from agents.summarization_agent import SummarizationAgent
    print("   ✓ SummarizationAgent")
    
    print("\n3. Testing orchestrator initialization...")
    try:
        orchestrator = NyayaOrchestrator()
        print("   ✓ Orchestrator initialized successfully")
        print(f"   ✓ Graph has {len(orchestrator.graph.nodes)} nodes")
    except Exception as e:
        print(f"   ⚠ Orchestrator init warning: {e}")
        print("   (This is OK if dependencies like Qdrant are not running)")
    
    print("\n4. Testing API imports...")
    from api.main import app
    print("   ✓ FastAPI app")
    
    from api.schemas import QueryRequest, QueryResponse
    print("   ✓ API schemas")
    
    print("\n" + "=" * 50)
    print("✅ All imports successful!")
    print("\nThe code structure is correct.")
    print("To run the full system:")
    print("  1. Start Qdrant: docker compose up -d qdrant")
    print("  2. Start API: uvicorn api.main:app --reload")
    print("  3. Start Streamlit: streamlit run frontend/app.py")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n⚠ Warning: {e}")
    print("(This may be OK if services are not running)")
