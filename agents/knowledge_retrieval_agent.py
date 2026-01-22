"""Legal Knowledge Retrieval Agent - Retrieves relevant statutes and laws."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding
from utils.tavily_search import get_tavily_search


class KnowledgeRetrievalAgent(BaseAgent):
    """Retrieves relevant legal statutes and regulations."""
    
    def __init__(self):
        super().__init__(
            name="legal_knowledge_retrieval",
            description="Retrieves relevant statutes, acts, and legal provisions"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Retrieve relevant legal knowledge.
        
        Args:
            input_data: Query with domain classification
            
        Returns:
            Retrieved statutes and legal provisions
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input",
                agent_name=self.name
            )
        
        # Get embedding and domain from context
        context = input_data.context or {}
        query_embedding = context.get("embedding")
        if not query_embedding:
            query_embedding = get_embedding(input_data.query)
        
        domains = context.get("domains", [])
        primary_domain = context.get("primary_domain", "general")
        
        # Search statutes collection
        filter_dict = None
        if primary_domain != "general":
            filter_dict = {"domain": primary_domain}
        
        statute_results = qdrant_manager.search(
            collection_name="statutes_vectors",
            query_vector=query_embedding,
            limit=5,
            score_threshold=0.5,
            filter_dict=filter_dict
        )
        
        self.log_retrieval("statutes_vectors", len(statute_results), 0.5)
        
        # Format retrieved statutes
        statutes = []
        for result in statute_results:
            statutes.append({
                "id": result["id"],
                "title": result["payload"].get("title", ""),
                "section": result["payload"].get("section", ""),
                "content": result["payload"].get("content", ""),
                "act_name": result["payload"].get("act_name", ""),
                "jurisdiction": result["payload"].get("jurisdiction", "india"),
                "score": result["score"]
            })
        
        confidence = statute_results[0]["score"] if statute_results else 0.0
        
        return AgentOutput(
            result={
                "statutes": all_statutes,
                "count": len(all_statutes)
            },
            retrieved_documents=statute_results + web_statutes,
            confidence=float(confidence),
            reasoning=f"Retrieved {len(statutes)} statute(s) from corpus and {len(web_statutes)} from web search",
            agent_name=self.name,
            metadata={
                "domain_filter": primary_domain,
                "collection": "statutes_vectors",
                "web_search_used": len(web_statutes) > 0
            }
        )
