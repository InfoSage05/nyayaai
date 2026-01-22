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
        self.model = "llama-3.1-8b-instant"
        
        # Enhanced synthesis-focused system prompt
        self.system_prompt = """You are a LEGAL & CIVIC INFORMATION ASSISTANT.

Your role is to explain legal and civic concepts in simple,
easy-to-understand language.

You may:
- Use general public legal knowledge
- Reason even when no documents are retrieved
- Summarize retrieved statutes and cases
- Combine web information with internal knowledge

You must:
- Clearly label whether information is:
  (a) General knowledge
  (b) Retrieved from internal database
  (c) Retrieved from web search
- Avoid legal advice
- Avoid procedural step-by-step instructions
- State limitations clearly
- Be neutral and factual

You must NEVER:
- Invent case law or statutes
- Pretend retrieved data exists when it does not
- Expose internal chain-of-thought"""

    def synthesize_legal_answer(
        self,
        query: str,
        retrieved_statutes: List[Dict[str, str]] = None,
        similar_cases: List[Dict[str, str]] = None,
        web_search_results: List[Dict[str, str]] = None,
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
                similar_cases or [],
                web_search_results or []
            )
            
            # Construct synthesis prompt
            prompt = f"""
User Query: {query}

Available Information:
{evidence_context}

TASK: Synthesize a comprehensive response that explains the legal topic in simple terms, like a helpful ChatGPT-style assistant.

REQUIRED OUTPUT SECTIONS:

[PLAIN LANGUAGE EXPLANATION]
Explain the topic in simple, everyday language (2-3 sentences)

[WHAT THE LAW GENERALLY SAYS]
Explain general legal principles from public knowledge

[RETRIEVED EVIDENCE]
Summarize any retrieved statutes or cases (only if available)

[SIMILAR CASE EXAMPLES]
Describe how similar cases typically proceed (only if available)

[WEB SOURCES]
Summarize web search findings with URLs (only if used)

[WHAT YOU CAN CONSIDER]
Non-advisory civic guidance about what people typically do

[DISCLAIMER]
Clear statement that this is not legal advice

Be helpful, clear, and comprehensive. Never say "no information found" - always provide general explanation."""
            
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
        cases: List[Dict[str, str]],
        web_results: List[Dict[str, str]] = None
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
        
        if web_results:
            context += "\nWEB SEARCH RESULTS:\n"
            for i, result in enumerate(web_results[:3], 1):  # Limit to top 3
                title = result.get("title", "Unknown")
                url = result.get("url", "")
                content = result.get("content", "No content")[:200]
                context += f"{i}. {title}\n   URL: {url}\n   {content}...\n\n"
        
        return context if context else "No specific evidence provided."

    def _parse_synthesis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM synthesis response into structured format."""
        try:
            sections = {
                "plain_language_explanation": "",
                "what_law_says": "",
                "retrieved_evidence": "",
                "similar_cases": "",
                "web_sources": "",
                "what_you_can_consider": "",
                "disclaimer": "",
                "full_response": response_text
            }
            
            # Parse sections
            if "[PLAIN LANGUAGE EXPLANATION]" in response_text:
                part = response_text.split("[PLAIN LANGUAGE EXPLANATION]")[1]
                if "[" in part:
                    sections["plain_language_explanation"] = part.split("[")[0].strip()
                else:
                    sections["plain_language_explanation"] = part.strip()
            
            if "[WHAT THE LAW GENERALLY SAYS]" in response_text:
                part = response_text.split("[WHAT THE LAW GENERALLY SAYS]")[1]
                if "[" in part:
                    sections["what_law_says"] = part.split("[")[0].strip()
                else:
                    sections["what_law_says"] = part.strip()
            
            if "[RETRIEVED EVIDENCE]" in response_text:
                part = response_text.split("[RETRIEVED EVIDENCE]")[1]
                if "[" in part:
                    sections["retrieved_evidence"] = part.split("[")[0].strip()
                else:
                    sections["retrieved_evidence"] = part.strip()
            
            if "[SIMILAR CASE EXAMPLES]" in response_text:
                part = response_text.split("[SIMILAR CASE EXAMPLES]")[1]
                if "[" in part:
                    sections["similar_cases"] = part.split("[")[0].strip()
                else:
                    sections["similar_cases"] = part.strip()
            
            if "[WEB SOURCES]" in response_text:
                part = response_text.split("[WEB SOURCES]")[1]
                if "[" in part:
                    sections["web_sources"] = part.split("[")[0].strip()
                else:
                    sections["web_sources"] = part.strip()
            
            if "[WHAT YOU CAN CONSIDER]" in response_text:
                part = response_text.split("[WHAT YOU CAN CONSIDER]")[1]
                if "[" in part:
                    sections["what_you_can_consider"] = part.split("[")[0].strip()
                else:
                    sections["what_you_can_consider"] = part.strip()
            
            if "[DISCLAIMER]" in response_text:
                sections["disclaimer"] = response_text.split("[DISCLAIMER]")[1].strip()
            
            # Determine confidence based on content
            confidence = "medium"
            if sections["retrieved_evidence"] or sections["similar_cases"] or sections["web_sources"]:
                confidence = "high"
            elif sections["what_law_says"]:
                confidence = "medium"
            else:
                confidence = "low"
            
            sections["confidence_level"] = confidence
            
            return sections
            
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
