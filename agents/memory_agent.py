"""Long-Term Case Memory Agent - Manages persistent case memory."""
from typing import Dict, Any, List
from datetime import datetime
import uuid
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding
from qdrant_client.models import PointStruct


class MemoryAgent(BaseAgent):
    """Manages long-term case memory and user interactions."""
    
    def __init__(self):
        super().__init__(
            name="long_term_memory",
            description="Stores and retrieves long-term case memory"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Store or retrieve case memory.
        
        Args:
            input_data: Query with full context to store/retrieve
            
        Returns:
            Memory operation result
        """
        context = input_data.context or {}
        operation = context.get("memory_operation", "store")  # "store" or "retrieve"
        
        if operation == "store":
            return self._store_memory(input_data, context)
        else:
            return self._retrieve_memory(input_data, context)
    
    def _store_memory(self, input_data: AgentInput, context: Dict[str, Any]) -> AgentOutput:
        """Store case memory in Qdrant."""
        # Generate case ID
        case_id = str(uuid.uuid4())
        
        # Build memory payload
        memory_data = {
            "case_id": case_id,
            "query": input_data.query,
            "domains": context.get("domains", []),
            "statutes": context.get("statutes", []),
            "cases": context.get("similar_cases", []),
            "explanation": context.get("explanation", ""),
            "recommendations": context.get("recommendations", []),
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.name,
            "source": "user_query"
        }
        
        # Generate embedding from query + explanation
        text_to_embed = f"{input_data.query} {context.get('explanation', '')}"
        embedding = get_embedding(text_to_embed)
        
        # Create point
        point = PointStruct(
            id=case_id,
            vector=embedding,
            payload=memory_data
        )
        
        # Store in case_memory_vectors collection
        success = qdrant_manager.upsert_points(
            collection_name="case_memory_vectors",
            points=[point]
        )
        
        # Also store in user_interaction_memory
        interaction_point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                **memory_data,
                "interaction_type": "query",
                "user_id": context.get("user_id", "anonymous")
            }
        )
        
        qdrant_manager.upsert_points(
            collection_name="user_interaction_memory",
            points=[interaction_point]
        )
        
        return AgentOutput(
            result={
                "case_id": case_id,
                "stored": success,
                "timestamp": memory_data["timestamp"]
            },
            confidence=1.0 if success else 0.0,
            reasoning=f"Case memory stored with ID: {case_id}",
            agent_name=self.name,
            metadata={"operation": "store"}
        )
    
    def _retrieve_memory(self, input_data: AgentInput, context: Dict[str, Any]) -> AgentOutput:
        """Retrieve similar past cases from memory."""
        case_id = context.get("case_id")
        
        if case_id:
            # Retrieve specific case
            query_embedding = get_embedding(input_data.query)
            results = qdrant_manager.search(
                collection_name="case_memory_vectors",
                query_vector=query_embedding,
                limit=5,
                score_threshold=0.5
            )
        else:
            # Search for similar cases
            query_embedding = context.get("embedding") or get_embedding(input_data.query)
            results = qdrant_manager.search(
                collection_name="case_memory_vectors",
                query_vector=query_embedding,
                limit=5,
                score_threshold=0.5
            )
        
        self.log_retrieval("case_memory_vectors", len(results), 0.5)
        
        memories = []
        for result in results:
            memories.append({
                "case_id": result["payload"].get("case_id", ""),
                "query": result["payload"].get("query", ""),
                "timestamp": result["payload"].get("timestamp", ""),
                "score": result["score"]
            })
        
        return AgentOutput(
            result={
                "memories": memories,
                "count": len(memories)
            },
            retrieved_documents=results,
            confidence=results[0]["score"] if results else 0.0,
            reasoning=f"Retrieved {len(memories)} case memory/ies",
            agent_name=self.name,
            metadata={"operation": "retrieve"}
        )
