"""Groq LLM Client - Synthesis Agent for Legal Information."""
import logging
from typing import Optional, List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

try:
    # Optional dependency: the app should still run (with fallbacks) if Groq isn't installed.
    from groq import Groq  # type: ignore
except ImportError:  # pragma: no cover
    Groq = None  # type: ignore


class GroqLLM:
    """Groq-based synthesis agent for legal information reasoning."""
    
    def __init__(self):
        """Initialize Groq client with API key from environment."""
        if Groq is None:
            raise ImportError(
                "Optional dependency 'groq' is not installed. "
                "Install it or configure the system to run in fallback mode."
            )
        self.api_key = settings.groq_api_key
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "mixtral-8x7b"
        
        # Synthesis-focused system prompt
        self.system_prompt = """You are a LEGAL INFORMATION SYNTHESIS AGENT.

CRITICAL RULES:
1. You do NOT provide legal advice
2. You synthesize ONLY based on provided evidence
3. You do NOT fabricate case law or statutes
4. You clearly state limitations and unknowns
5. You explain reasoning in simple terms
6. You identify patterns from evidence
7. You avoid procedural instructions
8. You maintain neutrality and accuracy

OUTPUT STRUCTURE:
- Start with a clear, simple explanation
- Identify patterns from the provided cases/statutes
- Explicitly state what is known and unknown
- Include relevant context
- Always include disclaimers about not being legal advice"""

    def synthesize_legal_answer(
        self,
        query: str,
        retrieved_statutes: List[Dict[str, str]] = None,
        similar_cases: List[Dict[str, str]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Synthesize a legal answer from evidence.
        
        This is the PRIMARY method called by the Orchestrator.
        It integrates all evidence into a coherent analysis.
        
        Args:
            query: The user's legal question
            retrieved_statutes: List of relevant statutes with summaries
            similar_cases: List of similar cases with outcomes
            temperature: Lower = more deterministic (0.2-0.5 recommended)
            max_tokens: Maximum response length
            
        Returns:
            Dict with summary, reasoning steps, confidence level
        """
        try:
            # Build evidence context
            evidence_context = self._build_evidence_context(
                retrieved_statutes or [],
                similar_cases or []
            )
            
            # Construct synthesis prompt
            prompt = f"""
LEGAL INFORMATION SYNTHESIS REQUEST

User Query:
{query}

Legal Context Provided:
{evidence_context}

TASK:
1. Explain the issue in simple, clear terms (2-3 sentences)
2. Identify key patterns from the provided statutes and cases
3. Clearly state:
   - What is known from the evidence
   - What is unclear or not covered by evidence
   - Any limitations or disclaimers
4. Suggest what steps a person might consider (without giving legal advice)

Format your response as:
[SUMMARY]
<2-3 sentence clear explanation>

[REASONING]
<Key patterns and connections from evidence>

[KNOWN & UNKNOWN]
<What the evidence covers and what it doesn't>

[IMPORTANT]
<Any disclaimers or limitations>
"""
            
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1.0,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse the structured response
            return self._parse_synthesis_response(result_text)
        
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return {
                "summary": "Unable to generate synthesis at this time.",
                "confidence_level": "low",
                "reasoning_steps": [],
                "limitations": "API error occurred",
                "error": str(e)
            }

    def _build_evidence_context(
        self,
        statutes: List[Dict[str, str]],
        cases: List[Dict[str, str]]
    ) -> str:
        """Build formatted evidence context for LLM."""
        context = ""
        
        if statutes:
            context += "RELEVANT STATUTES & ACTS:\n"
            for i, statute in enumerate(statutes[:5], 1):  # Limit to top 5
                title = statute.get("title", "Unknown")
                summary = statute.get("summary", statute.get("content", "No summary"))
                context += f"{i}. {title}\n   {summary[:300]}...\n\n"
        
        if cases:
            context += "\nSIMILAR CASES:\n"
            for i, case in enumerate(cases[:5], 1):  # Limit to top 5
                name = case.get("case_name", "Unknown")
                outcome = case.get("outcome", case.get("summary", "No details"))
                context += f"{i}. {name}\n   Outcome: {outcome[:200]}...\n\n"
        
        return context if context else "No specific evidence provided."

    def _parse_synthesis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM synthesis response into structured format."""
        try:
            sections = {
                "summary": "",
                "reasoning_steps": [],
                "limitations": "",
                "disclaimers": []
            }
            
            # Simple parsing of sections
            if "[SUMMARY]" in response_text:
                summary_part = response_text.split("[SUMMARY]")[1].split("[REASONING]")[0].strip()
                sections["summary"] = summary_part[:500]  # Limit to 500 chars
            
            if "[REASONING]" in response_text:
                reasoning_part = response_text.split("[REASONING]")[1].split("[KNOWN")[0].strip()
                sections["reasoning_steps"] = [s.strip() for s in reasoning_part.split("\n") if s.strip()]
            
            if "[IMPORTANT]" in response_text:
                important_part = response_text.split("[IMPORTANT]")[1].strip()
                sections["disclaimers"].append(important_part[:300])
            
            # Determine confidence based on evidence coverage
            confidence = "medium"
            if len(sections["reasoning_steps"]) > 3:
                confidence = "high"
            elif "unclear" in response_text.lower() or "unknown" in response_text.lower():
                confidence = "low"
            
            sections["confidence_level"] = confidence
            
            return sections
        
        except Exception as e:
            logger.error(f"Error parsing synthesis response: {e}")
            return {
                "summary": response_text[:500],
                "confidence_level": "low",
                "reasoning_steps": [],
                "limitations": "Parsing error",
                "error": str(e)
            }

    def generate_response(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> str:
        """Legacy method for backward compatibility.
        
        For new code, use synthesize_legal_answer() instead.
        """
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1.0,
            )
            
            result = response.choices[0].message.content
            if not result or not result.strip():
                logger.warning("Groq returned empty response")
                return "Unable to generate a response at this time."
            
            return result.strip()
        
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            logger.warning("Using fallback response due to API error")
            return "Based on the provided legal documents, here is relevant information about your query."


# Global Groq LLM instance
try:
    groq_llm = GroqLLM()
except (ValueError, ImportError) as e:
    logger.warning(f"Groq LLM unavailable; running in fallback mode: {e}")
    groq_llm = None
