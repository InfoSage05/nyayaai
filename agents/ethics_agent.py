"""Ethics & Safety Agent - Monitors outputs for safety and ethics."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput


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
        
        # Check for problematic content
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
            combined = f"{action} {description}"
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
            reasoning=f"Ethics check completed. Found {len(issues)} issue(s).",
            agent_name=self.name,
            metadata={
                "issues_count": len(issues),
                "validation_passed": is_safe
            }
        )
