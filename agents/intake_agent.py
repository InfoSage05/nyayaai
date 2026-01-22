"""Intake & Normalization Agent - Processes and normalizes user queries."""
from typing import Dict, Any
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from utils.embeddings import get_embedding


class IntakeAgent(BaseAgent):
    """Normalizes and preprocesses user queries."""
    
    def __init__(self):
        super().__init__(
            name="intake_normalization",
            description="Processes and normalizes user queries for downstream agents"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Normalize and preprocess query.
        
        Args:
            input_data: Raw user query
            
        Returns:
            Normalized query with metadata
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input: empty query",
                agent_name=self.name
            )
        
        query = input_data.query.strip()
        
        # Normalize: lowercase, remove extra spaces, basic cleanup
        normalized = " ".join(query.split())
        normalized = normalized.lower()
        
        # Extract basic metadata
        metadata = {
            "original_query": query,
            "normalized_query": normalized,
            "query_length": len(normalized),
            "word_count": len(normalized.split()),
            "language": "en"  # Default to English, can be extended
        }
        
        # Generate embedding for downstream use
        try:
            embedding = get_embedding(normalized)
            metadata["embedding_dim"] = len(embedding)
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            embedding = None
        
        return AgentOutput(
            result={
                "normalized_query": normalized,
                "embedding": embedding
            },
            confidence=1.0,
            reasoning="Query normalized and preprocessed successfully",
            agent_name=self.name,
            metadata=metadata
        )
