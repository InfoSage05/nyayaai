"""Handle LLM responses gracefully with fallback mechanisms using Groq."""
import logging
from typing import Optional, Dict, Any
from llm.groq_client import groq_llm

logger = logging.getLogger(__name__)


class RobustLLMClient:
    """Wrapper around Groq client with fallback mechanisms."""
    
    def __init__(self):
        self.groq = groq_llm
        self.max_retries = 3
        self.fallback_responses = {
            "explanation": "Based on the legal documents retrieved, here are the relevant provisions that apply to your query.",
            "reasoning": "The retrieved documents indicate important legal principles applicable to your situation.",
            "recommendation": "We recommend consulting the relevant statutes and seeking further guidance from legal professionals."
        }
    
    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> str:
        """Generate text with automatic fallback on failure using Groq."""
        
        try:
            # Combine system and user prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            result = self.groq.generate_response(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Validate response
            if result and result.strip() and "Error" not in result:
                logger.info(f"✓ Groq generated response")
                return result
            else:
                logger.warning(f"⚠ Groq returned empty/error response")
                return self.fallback_responses.get("explanation", "Unable to generate response at this time.")
                    
        except Exception as e:
            logger.warning(f"✗ Groq generation failed: {e}")
            logger.warning("⚠ Using fallback response")
            return self.fallback_responses.get("explanation", "Unable to generate response at this time.")
    
    def chat_with_fallback(
        self,
        messages: list,
        temperature: float = 0.2
    ) -> str:
        """Chat completion with fallback mechanism using Groq."""
        
        try:
            # Convert messages to prompt format
            prompt_parts = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role}: {content}")
            
            full_prompt = "\n".join(prompt_parts)
            
            result = self.groq.generate_response(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=1500
            )
            
            if result and result.strip() and "Error" not in result:
                logger.info(f"✓ Groq chat generated response")
                return result
            else:
                logger.warning(f"⚠ Groq chat returned empty/error")
                return self.fallback_responses.get("recommendation", "Unable to generate response at this time.")
                    
        except Exception as e:
            logger.warning(f"✗ Groq chat failed: {e}")
            logger.warning("⚠ Using fallback response")
            return self.fallback_responses.get("recommendation", "Unable to generate response at this time.")


# Global instance
robust_llm = RobustLLMClient()
