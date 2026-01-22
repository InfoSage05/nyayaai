"""Basic tests for NyayaAI."""
import pytest
from core.agent_base import AgentInput, AgentOutput
from agents.intake_agent import IntakeAgent


def test_intake_agent():
    """Test intake agent."""
    agent = IntakeAgent()
    input_data = AgentInput(query="How do I file an RTI application?")
    output = agent.process(input_data)
    
    assert output is not None
    assert output.agent_name == "intake_normalization"
    assert output.result is not None
    assert "normalized_query" in output.result


def test_intake_agent_empty_query():
    """Test intake agent with empty query."""
    agent = IntakeAgent()
    input_data = AgentInput(query="")
    output = agent.process(input_data)
    
    assert output.confidence == 0.0
    assert "Invalid" in output.reasoning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
