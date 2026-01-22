"""Base class for all agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class AgentInput(BaseModel):
    """Base input model for agents."""
    query: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentOutput(BaseModel):
    """Base output model for agents."""
    result: Any
    retrieved_documents: List[Dict[str, Any]] = []
    confidence: float = 0.0
    reasoning: str = ""
    agent_name: str = ""
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """Base class for all NyayaAI agents."""
    
    def __init__(self, name: str, description: str):
        """Initialize agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Process input and return output.
        
        Args:
            input_data: Agent input
            
        Returns:
            Agent output
        """
        pass
    
    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input data.
        
        Args:
            input_data: Agent input
            
        Returns:
            True if valid
        """
        if not input_data.query or not input_data.query.strip():
            self.logger.warning("Empty query received")
            return False
        return True
    
    def log_retrieval(self, collection: str, count: int, threshold: float):
        """Log retrieval operation.
        
        Args:
            collection: Qdrant collection name
            count: Number of documents retrieved
            threshold: Similarity threshold used
        """
        self.logger.info(
            f"Retrieved {count} documents from {collection} "
            f"(threshold: {threshold})"
        )
