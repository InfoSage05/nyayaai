"""Legal Reasoning Agent - Provides retrieval-bounded legal reasoning."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from llm.groq_client import groq_llm
from utils.tavily_search import get_tavily_search


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
        
        # Enhanced system prompt for retrieval-bounded legal reasoning
        system_prompt = """You are an expert legal reasoning assistant specializing in Indian law. Your task is to provide comprehensive legal analysis based ONLY on the provided documents.

CRITICAL REQUIREMENTS:
1. STRICT EVIDENCE-BASED REASONING: Only use information from the provided retrieved documents (statutes, cases, web resources)
2. PRECISE CITATIONS: Always cite specific statutes, sections, articles, case names, courts, and years when making legal claims
3. TRANSPARENCY: Clearly state when information is not available in the retrieved documents - never fabricate or assume
4. NO LEGAL ADVICE: Provide legal information and analysis, NOT legal advice or litigation strategy
5. CLARITY: Explain complex legal concepts in simple, accessible language that non-lawyers can understand
6. COMPREHENSIVE ANALYSIS: Address all aspects of the query, including:
   - Relevant legal provisions and their interpretation
   - How statutes apply to the situation
   - Precedents from similar cases
   - Recent legal developments (if available in sources)
   - Gaps or limitations in available information
7. STRUCTURED OUTPUT: Organize your response with clear sections, headings, and formatting
8. CONTEXT AWARENESS: Consider the broader legal framework and how different laws interact

OUTPUT FORMAT:
- Introduction: Brief overview of the legal area
- Relevant Legal Provisions: Specific statutes, sections, articles cited
- Case Law Analysis: How courts have interpreted and applied these laws
- Application to Query: How the law applies to the user's situation (informational)
- Limitations: What information is missing or unclear
- Important Notes: Disclaimers and caveats"""
        
        # Build enhanced user prompt with web search context if available
        web_context = context.get("web_search_results", [])
        web_info = ""
        if web_context:
            web_info = "\n\n=== RECENT LEGAL UPDATES & WEB SOURCES ===\n"
            for i, result in enumerate(web_context[:3], 1):
                web_info += f"{i}. {result.get('title', 'Unknown')}\n"
                web_info += f"   Source: {result.get('url', 'N/A')}\n"
                web_info += f"   Content: {result.get('content', '')[:200]}...\n\n"
        
        user_prompt = f"""User Query: {input_data.query}

=== RETRIEVED LEGAL DOCUMENTS ===
{retrieved_context}
{web_info}

TASK:
Based ONLY on the retrieved documents and web sources above, provide a comprehensive legal analysis that:

1. EXPLANATION: Clear, detailed explanation of relevant legal provisions, their interpretation, and application
2. STATUTE ANALYSIS: Specific statutes, sections, and articles cited with their relevance to the query
3. CASE LAW ANALYSIS: How courts have interpreted and applied these laws in similar situations
4. APPLICATION: How the law applies to the user's query (informational analysis, not advice)
5. RECENT DEVELOPMENTS: Any recent updates, amendments, or changes mentioned in web sources
6. GAPS & LIMITATIONS: What information is missing, unclear, or requires further research
7. CITATIONS: Precise citations to all statutes, cases, and sources used

IMPORTANT:
- Only use information from the provided documents and web sources
- Never fabricate, assume, or make up legal provisions
- If information is not available, clearly state that
- Maintain objectivity and neutrality
- Use clear, structured formatting with sections and headings"""

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
