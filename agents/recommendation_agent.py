"""Civic Action Recommendation Agent - Structured, actionable recommendations."""
from typing import Dict, Any, List, Set
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding
import logging

logger = logging.getLogger(__name__)


class RecommendationAgent(BaseAgent):
    """Generates structured, non-repetitive civic action recommendations."""
    
    def __init__(self):
        super().__init__(
            name="civic_action_recommendation",
            description="Generates structured, sequential civic action recommendations"
        )
        # Track actions to avoid duplication
        self._processed_actions: Set[str] = set()
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Generate structured civic recommendations.
        
        Args:
            input_data: Query with legal reasoning context
            
        Returns:
            Structured, non-duplicate civic action recommendations
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input",
                agent_name=self.name
            )
        
        context = input_data.context or {}
        query_embedding = context.get("embedding")
        if not query_embedding:
            query_embedding = get_embedding(input_data.query)
        
        primary_domain = context.get("primary_domain", "general")
        
        # Search civic processes collection
        filter_dict = None
        if primary_domain != "general":
            filter_dict = {"domain": primary_domain}
        
        process_results = qdrant_manager.search(
            collection_name="civic_process_vectors",
            query_vector=query_embedding,
            limit=10,  # Get more to filter duplicates
            score_threshold=0.4,
            filter_dict=filter_dict
        )
        
        self.log_retrieval("civic_process_vectors", len(process_results), 0.4)
        
        # STRUCTURED: Format and deduplicate recommendations
        recommendations = []
        seen_actions = set()
        
        for result in process_results:
            payload = result["payload"]
            action_name = payload.get("action", "").strip().lower()
            
            # Skip duplicates
            if action_name in seen_actions:
                logger.debug(f"Skipping duplicate action: {action_name}")
                continue
            
            seen_actions.add(action_name)
            
            structured_rec = {
                "action": payload.get("action", "Unnamed Action"),
                "responsible_authority": payload.get("authority", "Relevant Government Authority"),
                "why_this_matters": self._generate_why(payload, input_data.query),
                "next_step": self._generate_next_step(payload),
                "estimated_timeline": payload.get("timeline", "Varies by case"),
                "is_legal_advice": False,
                "sequence": len(recommendations) + 1,  # Sequential ordering
                "required_documents": payload.get("required_documents", []),
                "confidence": result["score"]
            }
            
            recommendations.append(structured_rec)
            
            # Limit to 5 unique recommendations
            if len(recommendations) >= 5:
                break
        
        confidence = process_results[0]["score"] if process_results else 0.0
        
        return AgentOutput(
            result={
                "recommendations": recommendations,
                "count": len(recommendations),
                "recommendation_summary": self._generate_summary(recommendations, input_data.query)
            },
            retrieved_documents=process_results,
            confidence=float(confidence),
            reasoning=f"Generated {len(recommendations)} unique, structured civic action(s)",
            agent_name=self.name,
            metadata={
                "domain_filter": primary_domain,
                "collection": "civic_process_vectors",
                "deduplication": "enabled",
                "max_results": 5,
                "structure": "action | authority | why | next_step | timeline"
            }
        )

    def _generate_why(self, payload: Dict[str, Any], query: str) -> str:
        """Generate explanation of why this action matters."""
        why = payload.get("importance", "")
        
        if why:
            return why[:200]
        
        # Fallback: explain based on action
        action = payload.get("action", "")
        if "RTI" in action.upper():
            return "This allows you to access information held by public authorities, which can help understand your case better."
        elif "petition" in action.lower() or "application" in action.lower():
            return "This formal step officially registers your case and starts the legal process."
        elif "appeal" in action.lower():
            return "This allows you to challenge a decision if you disagree with it."
        else:
            return "This is a key step in addressing your legal issue through proper channels."

    def _generate_next_step(self, payload: Dict[str, Any]) -> str:
        """Generate concrete next step for this action."""
        next_step = payload.get("next_step", "")
        
        if next_step:
            return next_step[:150]
        
        # Generate based on action
        action = payload.get("action", "")
        authority = payload.get("authority", "relevant authority")
        
        if "file" in action.lower() or "submit" in action.lower():
            docs = payload.get("required_documents", [])
            if docs:
                return f"Gather required documents: {', '.join(docs[:2])}. Then submit to {authority}."
            return f"Prepare application and submit to {authority}."
        elif "contact" in action.lower():
            return f"Identify the correct office of {authority} and reach out with your query."
        else:
            return f"Take this action through {authority}. Consult official channels for detailed steps."

    def _generate_summary(self, recommendations: List[Dict[str, Any]], query: str) -> str:
        """Generate summary of all recommendations."""
        if not recommendations:
            return "No specific civic actions identified for this query. Consult official channels."
        
        num_recs = len(recommendations)
        actions_list = "; ".join([r["action"] for r in recommendations[:3]])
        
        return (
            f"Recommended {num_recs} actionable step(s): {actions_list}. "
            f"These are presented in suggested order. "
            f"Note: This is informational guidance, not legal advice. "
            f"Consult appropriate authorities for case-specific guidance."
        )
