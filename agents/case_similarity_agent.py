"""Case Similarity Agent - Finds and structures similar past cases."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding
from llm.groq_client import groq_llm
import logging
import json

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
        
        # Step 1: Try LLM-based case analysis first
        self.logger.info("Attempting LLM-based case analysis...")
        structured_cases = self._llm_analyze_cases(
            query=input_data.query,
            case_results=case_results
        )
        analysis_method = "llm"
        
        # Step 2: If LLM fails, use template-based extraction
        if not structured_cases:
            self.logger.info("LLM analysis failed, using template-based fallback...")
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
                    "case_name": payload.get("case_name", "Unknown"),
                    "year": payload.get("year"),
                    "confidence": result["score"]
                }
                structured_cases.append(structured_case)
            analysis_method = "template"
        
        confidence = case_results[0]["score"] if case_results else 0.0
        if analysis_method == "llm":
            confidence = 0.8  # Higher confidence for LLM-analyzed
        
        return AgentOutput(
            result={
                "similar_cases": structured_cases,
                "count": len(structured_cases),
                "analysis_summary": self._generate_summary(structured_cases)
            },
            retrieved_documents=case_results,
            confidence=float(confidence),
            reasoning=f"Identified {len(structured_cases)} similar case(s) with structured analysis using {analysis_method}",
            agent_name=self.name,
            metadata={
                "analysis_method": analysis_method,
                "llm_used": analysis_method == "llm",
                "domain_filter": primary_domain,
                "collection": "case_law_vectors"
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
    
    def _llm_analyze_cases(self, query: str, case_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to analyze and structure retrieved cases.
        
        Args:
            query: User query
            case_results: List of retrieved case documents from Qdrant
            
        Returns:
            List of structured case analysis dictionaries
        """
        if groq_llm is None:
            self.logger.warning("Groq LLM not available for case analysis")
            return []
        
        if not case_results:
            return []
        
        try:
            # Build context from retrieved cases
            cases_context = []
            for i, case_result in enumerate(case_results[:5], 1):
                payload = case_result.get("payload", {})
                score = case_result.get("score", 0.0)
                cases_context.append(
                    f"{i}. Case: {payload.get('case_name', 'Unknown')} ({payload.get('year', 'N/A')})\n"
                    f"   Court: {payload.get('court', 'N/A')}\n"
                    f"   Summary: {payload.get('summary', '')[:300]}\n"
                    f"   Similarity Score: {score:.2f}"
                )
            
            system_prompt = """You are a legal case analysis assistant. Your task is to analyze similar past cases and structure them for user understanding.

For each case, provide:
1. case_context: What was the issue/context? (2-3 sentences)
2. what_happened: What actions were taken? (2-3 sentences)
3. outcome: What was the result/decision? (2-3 sentences)
4. relevance_to_query: Why is this case relevant to the user's query? (2-3 sentences)

Return a JSON array of case analysis objects. Maximum 5 cases.
Example format:
[
  {
    "case_context": "The case involved...",
    "what_happened": "The petitioner filed...",
    "outcome": "The court ruled...",
    "relevance_to_query": "This case is relevant because..."
  }
]

IMPORTANT: Base your analysis ONLY on the provided case information. Do not make up details."""

            user_prompt = f"""User Query: {query}

Retrieved Similar Cases:
{chr(10).join(cases_context)}

Analyze each case and provide structured information. Return ONLY a JSON array."""

            result = groq_llm.generate_response(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                temperature=0.3,
                max_tokens=2000
            )
            
            if not result:
                return []
            
            # Clean and parse JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
                result = result.strip()
            
            try:
                analyses = json.loads(result)
                if isinstance(analyses, list):
                    # Combine with original case data
                    structured = []
                    for i, analysis in enumerate(analyses[:5]):
                        if isinstance(analysis, dict) and i < len(case_results):
                            original_case = case_results[i]
                            payload = original_case.get("payload", {})
                            structured.append({
                                "case_context": analysis.get("case_context", ""),
                                "what_happened": analysis.get("what_happened", ""),
                                "outcome": analysis.get("outcome", ""),
                                "relevance_to_query": analysis.get("relevance_to_query", ""),
                                "source": payload.get("citation", payload.get("case_name", "")),
                                "case_name": payload.get("case_name", "Unknown"),
                                "year": payload.get("year"),
                                "confidence": original_case.get("score", 0.0)
                            })
                    if structured:
                        self.logger.info(f"✓ LLM analyzed {len(structured)} cases")
                        return structured
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse LLM JSON response for case analysis")
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error in LLM case analysis: {e}", exc_info=True)
            return []