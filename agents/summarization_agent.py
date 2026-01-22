"""Summarization Agent - Collects all agent outputs and generates unified final response."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from llm.groq_client import groq_llm
import logging

logger = logging.getLogger(__name__)


class SummarizationAgent(BaseAgent):
    """Collects outputs from all agents and generates a unified, coherent final response using LLM."""
    
    def __init__(self):
        """Initialize the Summarization Agent."""
        super().__init__(
            name="summarization",
            description="Synthesizes all agent outputs into a unified final response using LLM"
        )
    
    def _collect_agent_outputs(self, context: Dict[str, Any], agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and organize outputs from all previous agents.
        
        Args:
            context: The shared context from the orchestrator
            agent_outputs: Dictionary containing outputs from all agents
            
        Returns:
            Dictionary with organized agent outputs
        """
        collected = {
            "query": context.get("query", ""),
            "normalized_query": context.get("normalized_query", ""),
            "domains": context.get("domains", []),
            "primary_domain": context.get("primary_domain", "general"),
            "statutes": context.get("statutes", []),
            "similar_cases": context.get("similar_cases", []),
            "explanation": context.get("explanation", ""),
            "recommendations": context.get("recommendations", []),
            "ethics_check": context.get("ethics_check", {}),
            "intake_output": agent_outputs.get("intake", {}),
            "classification_output": agent_outputs.get("classification", {}),
            "knowledge_output": agent_outputs.get("knowledge", {}),
            "case_similarity_output": agent_outputs.get("case_similarity", {}),
            "reasoning_output": agent_outputs.get("reasoning", {}),
            "recommendation_output": agent_outputs.get("recommendation", {}),
            "ethics_output": agent_outputs.get("ethics", {})
        }
        
        self.logger.info(f"Collected outputs from {len(agent_outputs)} agents")
        return collected
    
    def _build_summarization_prompt(self, collected_outputs: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for LLM summarization.
        
        Args:
            collected_outputs: Dictionary with all agent outputs
            
        Returns:
            Formatted prompt string for LLM
        """
        query = collected_outputs.get("query", "")
        domains = collected_outputs.get("domains", [])
        statutes = collected_outputs.get("statutes", [])
        cases = collected_outputs.get("similar_cases", [])
        explanation = collected_outputs.get("explanation", "")
        recommendations = collected_outputs.get("recommendations", [])
        
        prompt_parts = [
            "=== USER QUERY ===",
            query,
            "",
            "=== LEGAL DOMAIN CLASSIFICATION ===",
            f"Primary Domain: {collected_outputs.get('primary_domain', 'general')}",
            f"All Domains: {', '.join(domains) if domains else 'Not classified'}",
            "",
            "=== RETRIEVED STATUTES ==="
        ]
        
        # Add statutes
        if statutes:
            for i, statute in enumerate(statutes[:5], 1):
                prompt_parts.append(
                    f"{i}. {statute.get('title', 'Unknown')} - "
                    f"Section {statute.get('section', 'N/A')}\n"
                    f"   {statute.get('content', '')[:300]}..."
                )
        else:
            prompt_parts.append("No relevant statutes found.")
        
        prompt_parts.append("")
        prompt_parts.append("=== SIMILAR CASES ===")
        
        # Add cases
        if cases:
            for i, case in enumerate(cases[:5], 1):
                prompt_parts.append(
                    f"{i}. {case.get('case_name', 'Unknown Case')} "
                    f"({case.get('year', 'N/A')})\n"
                    f"   Context: {case.get('case_context', '')[:200]}...\n"
                    f"   Outcome: {case.get('outcome', '')[:200]}..."
                )
        else:
            prompt_parts.append("No similar cases found.")
        
        prompt_parts.append("")
        prompt_parts.append("=== PRELIMINARY EXPLANATION ===")
        prompt_parts.append(explanation if explanation else "No explanation generated yet.")
        
        prompt_parts.append("")
        prompt_parts.append("=== CIVIC ACTION RECOMMENDATIONS ===")
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):
                prompt_parts.append(
                    f"{i}. {rec.get('action', 'Unknown Action')}\n"
                    f"   Authority: {rec.get('responsible_authority', 'N/A')}\n"
                    f"   Why: {rec.get('why_this_matters', '')[:150]}..."
                )
        else:
            prompt_parts.append("No recommendations generated.")
        
        prompt_parts.append("")
        prompt_parts.append("=== TASK ===")
        prompt_parts.append(
            "Based on ALL the information above from multiple agents, create a unified, "
            "coherent final response that:\n"
            "1. Provides a clear, comprehensive answer to the user's query\n"
            "2. Synthesizes information from statutes, cases, and recommendations\n"
            "3. Is written in simple, accessible language\n"
            "4. Includes relevant citations and references\n"
            "5. Clearly states what is known and what is unknown\n"
            "6. Includes appropriate disclaimers\n"
            "7. Is well-structured and easy to understand\n\n"
            "IMPORTANT: This is NOT legal advice. Provide information only."
        )
        
        return "\n".join(prompt_parts)
    
    def _call_llm_for_summarization(self, prompt: str) -> str:
        """Call LLM to generate unified summarization.
        
        Args:
            prompt: The formatted prompt for summarization
            
        Returns:
            Generated unified response from LLM
        """
        if groq_llm is None:
            self.logger.warning("Groq LLM not available for summarization")
            return None
        
        try:
            system_prompt = """You are a legal information synthesis assistant. Your task is to:
1. Synthesize information from multiple specialized agents
2. Create a unified, coherent response
3. Use simple, clear language
4. Cite specific sources (statutes, cases)
5. Clearly distinguish what is known vs unknown
6. Include appropriate disclaimers
7. NEVER provide legal advice or litigation strategy

Format your response as a clear, well-structured explanation."""
            
            result = groq_llm.generate_response(
                prompt=f"{system_prompt}\n\n{prompt}",
                temperature=0.3,
                max_tokens=2000
            )
            
            if result and result.strip():
                self.logger.info("✓ LLM summarization successful")
                return result.strip()
            else:
                self.logger.warning("LLM returned empty response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling LLM for summarization: {e}", exc_info=True)
            return None
    
    def _format_final_response(self, collected_outputs: Dict[str, Any], unified_summary: str) -> Dict[str, Any]:
        """Format the final unified response structure.
        
        Args:
            collected_outputs: All collected agent outputs
            unified_summary: The LLM-generated unified summary
            
        Returns:
            Formatted final response dictionary
        """
        return {
            "unified_summary": unified_summary,
            "query": collected_outputs.get("query", ""),
            "normalized_query": collected_outputs.get("normalized_query", ""),
            "legal_domain": collected_outputs.get("primary_domain", "general"),
            "domains": collected_outputs.get("domains", []),
            "statutes": collected_outputs.get("statutes", []),
            "similar_cases": collected_outputs.get("similar_cases", []),
            "recommendations": collected_outputs.get("recommendations", []),
            "ethics_check": collected_outputs.get("ethics_check", {}),
            "retrieval_evidence": {
                "statutes_count": len(collected_outputs.get("statutes", [])),
                "cases_count": len(collected_outputs.get("similar_cases", [])),
                "recommendations_count": len(collected_outputs.get("recommendations", []))
            },
            "disclaimers": {
                "safety": collected_outputs.get("ethics_check", {}).get("safety_disclaimer", ""),
                "standard": collected_outputs.get("ethics_check", {}).get("standard_disclaimer", 
                    "This information is for educational purposes only. It is not a substitute for professional legal advice.")
            },
            "agent_summary": {
                "intake": "Query normalized and preprocessed",
                "classification": f"Classified into {len(collected_outputs.get('domains', []))} domain(s)",
                "knowledge": f"Retrieved {len(collected_outputs.get('statutes', []))} statute(s)",
                "case_similarity": f"Found {len(collected_outputs.get('similar_cases', []))} similar case(s)",
                "reasoning": "Generated legal reasoning from retrieved documents",
                "recommendation": f"Generated {len(collected_outputs.get('recommendations', []))} recommendation(s)",
                "ethics": "Validated for safety and ethics"
            }
        }
    
    def _fallback_summarization(self, collected_outputs: Dict[str, Any]) -> str:
        """Generate fallback summary when LLM is unavailable.
        
        Args:
            collected_outputs: All collected agent outputs
            
        Returns:
            Fallback summary string
        """
        query = collected_outputs.get("query", "")
        domains = collected_outputs.get("domains", [])
        statutes_count = len(collected_outputs.get("statutes", []))
        cases_count = len(collected_outputs.get("similar_cases", []))
        recommendations_count = len(collected_outputs.get("recommendations", []))
        explanation = collected_outputs.get("explanation", "")
        
        summary_parts = [
            f"Based on your query: '{query}'",
            ""
        ]
        
        if domains:
            summary_parts.append(f"This query relates to: {', '.join(domains)}")
        
        summary_parts.append("")
        summary_parts.append("=== RETRIEVED INFORMATION ===")
        summary_parts.append(f"• Found {statutes_count} relevant statute(s)")
        summary_parts.append(f"• Found {cases_count} similar case(s)")
        summary_parts.append(f"• Generated {recommendations_count} recommendation(s)")
        
        if explanation:
            summary_parts.append("")
            summary_parts.append("=== EXPLANATION ===")
            summary_parts.append(explanation)
        
        # Add statutes summary
        statutes = collected_outputs.get("statutes", [])
        if statutes:
            summary_parts.append("")
            summary_parts.append("=== KEY STATUTES ===")
            for i, statute in enumerate(statutes[:3], 1):
                summary_parts.append(
                    f"{i}. {statute.get('title', 'Unknown')} - "
                    f"Section {statute.get('section', 'N/A')}"
                )
        
        # Add cases summary
        cases = collected_outputs.get("similar_cases", [])
        if cases:
            summary_parts.append("")
            summary_parts.append("=== SIMILAR CASES ===")
            for i, case in enumerate(cases[:3], 1):
                summary_parts.append(
                    f"{i}. {case.get('case_name', 'Unknown')} "
                    f"({case.get('year', 'N/A')})"
                )
        
        # Add recommendations summary
        recommendations = collected_outputs.get("recommendations", [])
        if recommendations:
            summary_parts.append("")
            summary_parts.append("=== RECOMMENDED ACTIONS ===")
            for i, rec in enumerate(recommendations[:3], 1):
                summary_parts.append(
                    f"{i}. {rec.get('action', 'Unknown Action')}"
                )
        
        summary_parts.append("")
        summary_parts.append("=== IMPORTANT DISCLAIMER ===")
        summary_parts.append(
            "This information is for educational purposes only. "
            "It is not legal advice. Consult a qualified lawyer for specific legal matters."
        )
        
        return "\n".join(summary_parts)
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Main process method that orchestrates summarization.
        
        Args:
            input_data: Agent input with query and context containing all agent outputs
            
        Returns:
            AgentOutput with unified final response
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input: empty query",
                agent_name=self.name
            )
        
        try:
            context = input_data.context or {}
            agent_outputs = context.get("agent_outputs", {})
            
            # Step 1: Collect all agent outputs
            self.logger.info("Collecting outputs from all agents...")
            collected_outputs = self._collect_agent_outputs(context, agent_outputs)
            
            # Step 2: Build summarization prompt
            self.logger.info("Building summarization prompt...")
            prompt = self._build_summarization_prompt(collected_outputs)
            
            # Step 3: Call LLM for summarization
            self.logger.info("Calling LLM for unified summarization...")
            unified_summary = self._call_llm_for_summarization(prompt)
            
            # Step 4: If LLM failed, use fallback
            if not unified_summary:
                self.logger.warning("LLM summarization failed, using fallback")
                unified_summary = self._fallback_summarization(collected_outputs)
            
            # Step 5: Format final response
            self.logger.info("Formatting final response...")
            final_response = self._format_final_response(collected_outputs, unified_summary)
            
            # Calculate confidence based on available information
            confidence = self._calculate_confidence(collected_outputs)
            
            return AgentOutput(
                result=final_response,
                confidence=confidence,
                reasoning="Successfully synthesized unified response from all agent outputs",
                agent_name=self.name,
                metadata={
                    "llm_used": unified_summary is not None and groq_llm is not None,
                    "agents_synthesized": len(agent_outputs),
                    "statutes_count": len(collected_outputs.get("statutes", [])),
                    "cases_count": len(collected_outputs.get("similar_cases", []))
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in summarization agent: {e}", exc_info=True)
            return AgentOutput(
                result={
                    "unified_summary": f"Error generating unified response: {str(e)}",
                    "query": input_data.query,
                    "error": str(e)
                },
                confidence=0.0,
                reasoning=f"Error occurred: {str(e)}",
                agent_name=self.name
            )
    
    def _calculate_confidence(self, collected_outputs: Dict[str, Any]) -> float:
        """Calculate confidence score based on available information.
        
        Args:
            collected_outputs: All collected agent outputs
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        statutes_count = len(collected_outputs.get("statutes", []))
        cases_count = len(collected_outputs.get("similar_cases", []))
        recommendations_count = len(collected_outputs.get("recommendations", []))
        has_explanation = bool(collected_outputs.get("explanation"))
        has_domains = bool(collected_outputs.get("domains"))
        
        # Base confidence
        confidence = 0.3
        
        # Add points for each component
        if has_domains:
            confidence += 0.1
        if statutes_count > 0:
            confidence += min(0.2, statutes_count * 0.05)
        if cases_count > 0:
            confidence += min(0.2, cases_count * 0.05)
        if recommendations_count > 0:
            confidence += min(0.1, recommendations_count * 0.02)
        if has_explanation:
            confidence += 0.1
        
        return min(confidence, 1.0)
