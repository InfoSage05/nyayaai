"""LLM utilities - wrapper for Groq client."""
import logging
from typing import Optional, Dict, Any, List

from llm.groq_client import groq_llm

logger = logging.getLogger(__name__)


class GroqClientWrapper:
    """Wrapper for Groq LLM client for backward compatibility."""
    
    def __init__(self):
        self.groq = groq_llm
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> str:
        """Generate text using Groq.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (added to prompt for Groq)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            # Combine system prompt with user prompt for Groq
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            result = self.groq.generate_response(
                prompt=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return result if result else "Unable to generate response."
        
        except Exception as e:
            logger.error(f"Error generating with Groq: {e}")
            return f"Error: Could not generate response. {str(e)}"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2
    ) -> str:
        """Chat completion using Groq.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Assistant response
        """
        try:
            # Convert messages to prompt format for Groq
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
            return result if result else "Unable to generate response."
        
        except Exception as e:
            logger.error(f"Error in Groq chat: {e}")
            return f"Error: Could not generate response. {str(e)}"


# Global Groq client wrapper instance (backward compatibility)
ollama_client = GroqClientWrapper()
