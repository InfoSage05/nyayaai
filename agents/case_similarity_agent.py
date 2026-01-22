"""Case Similarity Agent - Finds and structures similar past cases."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding
import logging

logger = logging.getLogger(__name__)


class CaseSimilarityAgent(BaseAgent):
    """Finds similar past cases and structures them for analysis."""
    
    def __init__(self):
        super().__init__(
            name="case_similarity",
            description="Retrieves and structures similar past cases for reference"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Find and structure similar cases.
        
        Args:
            input_data: Query with domain and statutes context
            
        Returns:
            Structured similar case analyses (not raw text)
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
        
        primary_domain = context.get("primary_domain", "general")
        
        # Search case law collection
        filter_dict = None
        if primary_domain != "general":
            filter_dict = {"domain": primary_domain}
        
        case_results = qdrant_manager.search(
            collection_name="case_law_vectors",
            query_vector=query_embedding,
            limit=5,
            score_threshold=0.5,
            filter_dict=filter_dict
        )
        
        self.log_retrieval("case_law_vectors", len(case_results), 0.5)
        
        # STRUCTURED: Analyze and format retrieved cases
        structured_cases = []
        for result in case_results:
            payload = result["payload"]
            structured_case = {
                "case_context": self._extract_context(payload),
                "what_happened": self._extract_action(payload),
                "outcome": self._extract_outcome(payload),
                "relevance_to_query": self._determine_relevance(
                    input_data.query,
                    payload,
                    result["score"]
                ),
                "source": payload.get("citation", payload.get("case_name", "")),
                "confidence": result["score"]
            }
            structured_cases.append(structured_case)
        
        confidence = case_results[0]["score"] if case_results else 0.0
        
        return AgentOutput(
            result={
                "similar_cases": structured_cases,
                "count": len(structured_cases),
                "analysis_summary": self._generate_summary(structured_cases)
            },
            retrieved_documents=case_results,
            confidence=float(confidence),
            reasoning=f"Identified {len(structured_cases)} similar case(s) with structured analysis",
            agent_name=self.name,
            metadata={
                "domain_filter": primary_domain,
                "collection": "case_law_vectors",
                "structure": "context | what_happened | outcome | relevance"
            }
        )

    def _extract_context(self, payload: Dict[str, Any]) -> str:
        """Extract 'what was the issue about?' from case payload."""
        # Try multiple possible fields
        context = (
            payload.get("context", "")
            or payload.get("issue", "")
            or payload.get("facts", "")
        )
        if context:
            return context[:200]
        
        # Fallback to summary beginning
        summary = payload.get("summary", "")
        return summary[:200] if summary else "Issue not specified"

    def _extract_action(self, payload: Dict[str, Any]) -> str:
        """Extract 'what actions were taken?' from case payload."""
        action = (
            payload.get("action", "")
            or payload.get("proceedings", "")
            or payload.get("relief_sought", "")
        )
        if action:
            return action[:250]
        
        # Fallback to middle of summary
        summary = payload.get("summary", "")
        if len(summary) > 200:
            return summary[100:350]
        return "Actions not detailed in record"

    def _extract_outcome(self, payload: Dict[str, Any]) -> str:
        """Extract 'what was the result?' from case payload."""
        outcome = (
            payload.get("outcome", "")
            or payload.get("judgment", "")
            or payload.get("ruling", "")
            or payload.get("decision", "")
        )
        if outcome:
            return outcome[:250]
        
        # Fallback to end of summary
        summary = payload.get("summary", "")
        if len(summary) > 300:
            return summary[-250:]
        return "Outcome not specified"

    def _determine_relevance(
        self,
        query: str,
        payload: Dict[str, Any],
        similarity_score: float
    ) -> str:
        """Explain why this case is relevant to the query."""
        # Determine relevance based on similarity and content
        if similarity_score > 0.85:
            relevance_level = "Highly relevant"
        elif similarity_score > 0.70:
            relevance_level = "Moderately relevant"
        else:
            relevance_level = "Potentially relevant"
        
        # Try to find connecting factors
        case_name = payload.get("case_name", "Case")
        case_domain = payload.get("domain", "").lower()
        
        return (
            f"{relevance_level} ({similarity_score:.2f}). "
            f"Similar because: {case_name} involves comparable legal principles. "
            f"Can help understand potential precedents and outcomes."
        )

    def _generate_summary(self, structured_cases: List[Dict[str, Any]]) -> str:
        """Generate high-level summary of case analysis."""
        if not structured_cases:
            return "No similar past cases found in database."
        
        num_cases = len(structured_cases)
        high_confidence = sum(1 for c in structured_cases if c.get("confidence", 0) > 0.8)
        
        return (
            f"Found {num_cases} similar past case(s). "
            f"{high_confidence} have high relevance. "
            f"These cases provide context for understanding potential legal outcomes. "
            f"Note: These are informational examples, not precedent binding."
        )
