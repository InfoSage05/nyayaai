"""Legal Reasoning Agent - Provides retrieval-bounded legal reasoning."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from llm.groq_client import groq_llm


class ReasoningAgent(BaseAgent):
    """Provides legal reasoning based on retrieved documents (no hallucination)."""
    
    def __init__(self):
        super().__init__(
            name="legal_reasoning",
            description="Provides retrieval-bounded legal reasoning and explanations"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Generate legal reasoning from retrieved documents.
        
        Args:
            input_data: Query with retrieved statutes and cases
            
        Returns:
            Reasoning and explanation grounded in retrieved documents
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input",
                agent_name=self.name
            )
        
        context = input_data.context or {}
        statutes = context.get("statutes", [])
        cases = context.get("similar_cases", [])
        
        # Build context from retrieved documents
        retrieved_context = self._build_context(statutes, cases)
        
        if not retrieved_context:
            return AgentOutput(
                result={
                    "explanation": "No relevant legal documents were found to base reasoning on.",
                    "reasoning": "Cannot provide reasoning without retrieval evidence."
                },
                confidence=0.0,
                reasoning="No retrieved documents available for reasoning",
                agent_name=self.name
            )
        
        # System prompt enforcing retrieval-bounded behavior
        system_prompt = """You are a legal information assistant. You MUST:
1. Only use information from the provided retrieved documents
2. Cite specific statutes, sections, and cases when making claims
3. Clearly state when information is not available in the retrieved documents
4. NEVER provide legal advice or litigation strategy
5. Explain legal concepts in simple language
6. Indicate what is known and what is unknown"""
        
        # Build user prompt
        user_prompt = f"""User Query: {input_data.query}

Retrieved Legal Documents:
{retrieved_context}

Based ONLY on the retrieved documents above, provide:
1. A clear explanation of relevant legal provisions
2. How they apply to the user's query
3. What information is missing or unclear
4. Citations to specific statutes/cases used

Remember: Only use information from the retrieved documents. Do not make up or assume legal provisions."""

        # Generate reasoning
        explanation = None
        try:
            if groq_llm is None:
                self.logger.error("Groq LLM not initialized")
                explanation = None
            else:
                result = groq_llm.generate_response(
                    prompt=f"{system_prompt}\n\n{user_prompt}",
                    temperature=0.2,
                    max_tokens=1500
                )
                explanation = result if result else None
                
                if not explanation:
                    self.logger.warning("Groq returned empty/None response")
        except Exception as e:
            self.logger.error(f"Error generating reasoning with Groq: {e}", exc_info=True)
            explanation = None
        
        # Fallback if Groq failed
        if not explanation:
            self.logger.warning("Using fallback explanation")
            explanation = f"Based on the {len(statutes)} retrieved statutes and {len(cases)} similar cases, here are the relevant legal provisions that apply to your query. Please review the documents above for specific details."
        
        # Calculate confidence based on retrieved document quality
        confidence = self._calculate_confidence(statutes, cases)
        
        return AgentOutput(
            result={
                "explanation": explanation,
                "statutes_cited": [s.get("title", "") for s in statutes[:3]],
                "cases_cited": [c.get("case_name", "") for c in cases[:3]]
            },
            retrieved_documents=statutes + cases,
            confidence=confidence,
            reasoning="Generated retrieval-bounded legal reasoning",
            agent_name=self.name,
            metadata={
                "statutes_count": len(statutes),
                "cases_count": len(cases),
                "reasoning_bounded": True
            }
        )
    
    def _build_context(self, statutes: List[Dict], cases: List[Dict]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        
        if statutes:
            context_parts.append("=== STATUTES ===")
            for i, statute in enumerate(statutes[:3], 1):
                context_parts.append(
                    f"{i}. {statute.get('act_name', 'Unknown Act')} - "
                    f"Section {statute.get('section', 'N/A')}\n"
                    f"   {statute.get('content', '')[:300]}..."
                )
        
        if cases:
            context_parts.append("\n=== SIMILAR CASES ===")
            for i, case in enumerate(cases[:3], 1):
                context_parts.append(
                    f"{i}. {case.get('case_name', 'Unknown Case')} "
                    f"({case.get('year', 'N/A')})\n"
                    f"   Court: {case.get('court', 'N/A')}\n"
                    f"   Summary: {case.get('summary', '')[:300]}..."
                )
        
        return "\n".join(context_parts)
    
    def _calculate_confidence(self, statutes: List[Dict], cases: List[Dict]) -> float:
        """Calculate confidence based on retrieved document quality."""
        if not statutes and not cases:
            return 0.0
        
        # Average scores from retrieved documents
        scores = []
        for statute in statutes:
            scores.append(statute.get("score", 0.0))
        for case in cases:
            scores.append(case.get("score", 0.0))
        
        if scores:
            avg_score = sum(scores) / len(scores)
            # Normalize to 0-1 range
            return min(avg_score, 1.0)
        
        return 0.5
