"""Ethics & Safety Agent - Monitors outputs for safety and ethics."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from llm.groq_client import groq_llm
import json
import logging

logger = logging.getLogger(__name__)


class EthicsAgent(BaseAgent):
    """Monitors and validates outputs for ethics and safety."""
    
    def __init__(self):
        super().__init__(
            name="ethics_safety",
            description="Monitors outputs for ethical compliance and safety"
        )
        # Keywords that indicate problematic content
        self.problematic_keywords = [
            "sue them",
            "file a lawsuit",
            "litigation strategy",
            "legal advice",
            "guaranteed win",
            "definitely illegal",
            "you should sue"
        ]
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Validate output for ethics and safety.
        
        Args:
            input_data: Final output to validate
            
        Returns:
            Validation result with flags and modifications
        """
        context = input_data.context or {}
        
        # Extract text to check
        explanation = context.get("explanation", "")
        recommendations = context.get("recommendations", [])
        
        # Step 1: Try LLM-based safety check first
        self.logger.info("Attempting LLM-based safety check...")
        llm_result = self._llm_check_safety(explanation, recommendations)
        check_method = llm_result.get("method", "keyword")
        
        if check_method == "llm":
            is_safe = llm_result.get("is_safe", True)
            issues = llm_result.get("issues", [])
        else:
            # Step 2: Fallback to keyword matching
            self.logger.info("LLM check unavailable, using keyword matching fallback...")
            issues = []
            is_safe = True
            
            # Check explanation
            explanation_lower = explanation.lower()
            for keyword in self.problematic_keywords:
                if keyword in explanation_lower:
                    issues.append(f"Found problematic phrase: '{keyword}'")
                    is_safe = False
            
            # Check recommendations
            for rec in recommendations:
                action = rec.get("action", "").lower()
                description = rec.get("description", "").lower()
                why = rec.get("why_this_matters", "").lower()
                combined = f"{action} {description} {why}"
                for keyword in self.problematic_keywords:
                    if keyword in combined:
                        issues.append(f"Problematic content in recommendation: '{keyword}'")
                        is_safe = False
        
        # Add safety disclaimers if needed
        safety_disclaimer = ""
        if not is_safe:
            safety_disclaimer = (
                "\n\n⚠️ IMPORTANT DISCLAIMER: "
                "This system provides legal information only, not legal advice. "
                "Consult a qualified lawyer for specific legal matters. "
                "This system does not provide litigation strategies or guarantee outcomes."
            )
        
        # Always add standard disclaimer
        standard_disclaimer = (
            "\n\n📋 Note: This information is for educational purposes only. "
            "It is not a substitute for professional legal advice."
        )
        
        return AgentOutput(
            result={
                "is_safe": is_safe,
                "issues": issues,
                "safety_disclaimer": safety_disclaimer,
                "standard_disclaimer": standard_disclaimer,
                "approved": is_safe
            },
            confidence=1.0 if is_safe else 0.5,
            reasoning=f"Ethics check completed using {check_method}. Found {len(issues)} issue(s).",
            agent_name=self.name,
            metadata={
                "check_method": check_method,
                "llm_used": check_method == "llm",
                "issues_count": len(issues),
                "validation_passed": is_safe
            }
        )
    
    def _llm_check_safety(self, explanation: str, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to check for safety and ethics issues.
        
        Args:
            explanation: The explanation text to check
            recommendations: List of recommendations to check
            
        Returns:
            Dictionary with safety check results
        """
        if groq_llm is None:
            self.logger.warning("Groq LLM not available for safety checking")
            return {"is_safe": True, "issues": [], "method": "keyword"}
        
        try:
            # Build content to check
            content_to_check = f"Explanation: {explanation}\n\n"
            if recommendations:
                content_to_check += "Recommendations:\n"
                for i, rec in enumerate(recommendations[:5], 1):
                    content_to_check += f"{i}. {rec.get('action', '')}: {rec.get('why_this_matters', '')}\n"
            
            system_prompt = """You are an expert safety and ethics validator for a legal information system. Your critical task is to ensure all content adheres to strict safety, ethical, and legal compliance standards.

VALIDATION CRITERIA - CHECK FOR:
1. LEGAL ADVICE: Does the content provide legal advice? (MUST NOT)
2. LITIGATION STRATEGY: Does it suggest litigation strategies, court tactics, or legal maneuvers? (MUST NOT)
3. GUARANTEES: Does it make guarantees, promises, or predictions about legal outcomes? (MUST NOT)
4. MISLEADING LANGUAGE: Does it use language that could mislead users about their legal situation?
5. UNSAFE CONTENT: Does it contain content that could lead to harmful actions or legal risks?
6. INACCURACIES: Does it contain factual inaccuracies, fabricated laws, or made-up case law?
7. DISCLAIMERS: Are appropriate disclaimers present and clear?
8. PROFESSIONAL BOUNDARIES: Does it overstep boundaries by providing specific legal counsel?

VALIDATION STANDARDS:
- Content should provide legal INFORMATION, not legal ADVICE
- Content should be educational and informational
- Content should include appropriate disclaimers
- Content should maintain neutrality and objectivity
- Content should not suggest specific legal actions or strategies

OUTPUT FORMAT:
Return a JSON object with:
{
  "is_safe": true/false,
  "issues": ["list of specific, detailed issues found"],
  "reasoning": "comprehensive explanation of the safety assessment",
  "severity": "low/medium/high" (if issues found)
}

If content is safe, return is_safe: true and empty issues array with reasoning explaining why it's safe."""

            user_prompt = f"""Check this content for safety and ethics issues:

{content_to_check}

Analyze and return JSON with safety assessment."""

            result = groq_llm.generate_response(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                temperature=0.2,
                max_tokens=500
            )
            
            if not result:
                return {"is_safe": True, "issues": [], "method": "keyword"}
            
            # Clean and parse JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
                result = result.strip()
            
            try:
                check_result = json.loads(result)
                if isinstance(check_result, dict):
                    check_result["method"] = "llm"
                    self.logger.info(f"✓ LLM safety check: {'safe' if check_result.get('is_safe') else 'issues found'}")
                    return check_result
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse LLM safety check response")
            
            return {"is_safe": True, "issues": [], "method": "keyword"}
            
        except Exception as e:
            self.logger.error(f"Error in LLM safety check: {e}", exc_info=True)
            return {"is_safe": True, "issues": [], "method": "keyword"}