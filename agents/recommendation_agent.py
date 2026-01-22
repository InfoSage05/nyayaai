"""Civic Action Recommendation Agent - Structured, actionable recommendations."""
from typing import Dict, Any, List, Set
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding
from llm.groq_client import groq_llm
import logging
import json

logger = logging.getLogger(__name__)


class RecommendationAgent(BaseAgent):
    """Generates structured, non-repetitive civic action recommendations."""
    
    def __init__(self):
        super().__init__(
            name="civic_action_recommendation",
            description="Generates structured, sequential civic action recommendations"
        )
        # Track actions to avoid duplication
        self._processed_actions: Set[str] = set()
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Generate structured civic recommendations.
        
        Args:
            input_data: Query with legal reasoning context
            
        Returns:
            Structured, non-duplicate civic action recommendations
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input",
                agent_name=self.name
            )
        
        context = input_data.context or {}
        query_embedding = context.get("embedding")
        if not query_embedding:
            query_embedding = get_embedding(input_data.query)
        
        primary_domain = context.get("primary_domain", "general")
        
        # Search civic processes collection
        filter_dict = None
        if primary_domain != "general":
            filter_dict = {"domain": primary_domain}
        
        process_results = qdrant_manager.search(
            collection_name="civic_process_vectors",
            query_vector=query_embedding,
            limit=10,  # Get more to filter duplicates
            score_threshold=0.4,
            filter_dict=filter_dict
        )
        
        self.log_retrieval("civic_process_vectors", len(process_results), 0.4)
        
        # Step 1: Try LLM-based recommendation generation first
        self.logger.info("Attempting LLM-based recommendation generation...")
        recommendations = self._llm_generate_recommendations(
            query=input_data.query,
            retrieved_processes=process_results,
            context=context
        )
        generation_method = "llm"
        
        # Step 2: If LLM fails, use template-based generation
        if not recommendations:
            self.logger.info("LLM generation failed, using template-based fallback...")
            recommendations = []
            seen_actions = set()
            
            for result in process_results:
                payload = result["payload"]
                action_name = payload.get("action", "").strip().lower()
                
                # Skip duplicates
                if action_name in seen_actions:
                    logger.debug(f"Skipping duplicate action: {action_name}")
                    continue
                
                seen_actions.add(action_name)
                
                structured_rec = {
                    "action": payload.get("action", "Unnamed Action"),
                    "responsible_authority": payload.get("authority", "Relevant Government Authority"),
                    "why_this_matters": self._generate_why(payload, input_data.query),
                    "next_step": self._generate_next_step(payload),
                    "estimated_timeline": payload.get("timeline", "Varies by case"),
                    "is_legal_advice": False,
                    "sequence": len(recommendations) + 1,
                    "required_documents": payload.get("required_documents", []),
                    "confidence": result["score"]
                }
                
                recommendations.append(structured_rec)
                
                # Limit to 5 unique recommendations
                if len(recommendations) >= 5:
                    break
            
            generation_method = "template"
        
        confidence = process_results[0]["score"] if process_results else 0.0
        if generation_method == "llm":
            confidence = 0.8  # Higher confidence for LLM-generated
        
        return AgentOutput(
            result={
                "recommendations": recommendations,
                "count": len(recommendations),
                "recommendation_summary": self._generate_summary(recommendations, input_data.query)
            },
            retrieved_documents=process_results,
            confidence=float(confidence),
            reasoning=f"Generated {len(recommendations)} unique, structured civic action(s) using {generation_method}",
            agent_name=self.name,
            metadata={
                "generation_method": generation_method,
                "llm_used": generation_method == "llm",
                "domain_filter": primary_domain,
                "collection": "civic_process_vectors",
                "deduplication": "enabled",
                "max_results": 5
            }
        )

    def _generate_why(self, payload: Dict[str, Any], query: str) -> str:
        """Generate explanation of why this action matters."""
        why = payload.get("importance", "")
        
        if why:
            return why[:200]
        
        # Fallback: explain based on action
        action = payload.get("action", "")
        if "RTI" in action.upper():
            return "This allows you to access information held by public authorities, which can help understand your case better."
        elif "petition" in action.lower() or "application" in action.lower():
            return "This formal step officially registers your case and starts the legal process."
        elif "appeal" in action.lower():
            return "This allows you to challenge a decision if you disagree with it."
        else:
            return "This is a key step in addressing your legal issue through proper channels."

    def _generate_next_step(self, payload: Dict[str, Any]) -> str:
        """Generate concrete next step for this action."""
        next_step = payload.get("next_step", "")
        
        if next_step:
            return next_step[:150]
        
        # Generate based on action
        action = payload.get("action", "")
        authority = payload.get("authority", "relevant authority")
        
        if "file" in action.lower() or "submit" in action.lower():
            docs = payload.get("required_documents", [])
            if docs:
                return f"Gather required documents: {', '.join(docs[:2])}. Then submit to {authority}."
            return f"Prepare application and submit to {authority}."
        elif "contact" in action.lower():
            return f"Identify the correct office of {authority} and reach out with your query."
        else:
            return f"Take this action through {authority}. Consult official channels for detailed steps."

    def _generate_summary(self, recommendations: List[Dict[str, Any]], query: str) -> str:
        """Generate summary of all recommendations."""
        if not recommendations:
            return "No specific civic actions identified for this query. Consult official channels."
        
        num_recs = len(recommendations)
        actions_list = "; ".join([r["action"] for r in recommendations[:3]])
        
        return (
            f"Recommended {num_recs} actionable step(s): {actions_list}. "
            f"These are presented in suggested order. "
            f"Note: This is informational guidance, not legal advice. "
            f"Consult appropriate authorities for case-specific guidance."
        )
    
    def _llm_generate_recommendations(self, query: str, retrieved_processes: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to generate structured recommendations from retrieved processes.
        
        Args:
            query: User query
            retrieved_processes: List of retrieved civic process documents
            context: Additional context (statutes, cases, etc.)
            
        Returns:
            List of structured recommendation dictionaries
        """
        if groq_llm is None:
            self.logger.warning("Groq LLM not available for recommendation generation")
            return []
        
        if not retrieved_processes:
            return []
        
        try:
            # Build context from retrieved processes
            processes_context = []
            for i, proc in enumerate(retrieved_processes[:10], 1):
                payload = proc.get("payload", {})
                processes_context.append(
                    f"{i}. Action: {payload.get('action', 'Unknown')}\n"
                    f"   Authority: {payload.get('authority', 'N/A')}\n"
                    f"   Description: {payload.get('description', '')[:200]}\n"
                    f"   Steps: {', '.join(payload.get('steps', [])[:3])}\n"
                    f"   Timeline: {payload.get('timeline', 'N/A')}"
                )
            
            system_prompt = """You are an expert civic action recommendation assistant specializing in Indian legal and administrative processes. Your task is to generate structured, actionable, and practical recommendations based on retrieved civic processes and legal context.

RECOMMENDATION REQUIREMENTS:
For each recommendation, provide comprehensive information:
1. action: Clear, specific action name
2. responsible_authority: Which authority, department, or office handles this (be specific)
3. why_this_matters: Why this action is important and how it addresses the user's query (2-3 sentences)
4. next_step: Concrete, actionable next step the user should take (2-3 sentences with specific details)
5. estimated_timeline: Expected timeline, processing time, or response time if available
6. required_documents: List of documents or information needed (if applicable)
7. contact_info: How to contact the relevant authority (if available)

OUTPUT FORMAT:
Return a JSON array of recommendation objects. Maximum 5 recommendations, prioritized by relevance and practicality.

Example format:
[
  {
    "action": "File RTI Application under Right to Information Act, 2005",
    "responsible_authority": "Public Information Officer (PIO) of the relevant public authority",
    "why_this_matters": "The RTI Act empowers citizens to access information held by public authorities. This action allows you to obtain specific information related to your query, promoting transparency and accountability in governance.",
    "next_step": "Prepare a written RTI application with specific questions, pay the prescribed fee (Rs. 10), and submit it to the PIO of the relevant public authority either in person, by post, or online through the RTI portal.",
    "estimated_timeline": "30 days for response (45 days if information concerns life or liberty)",
    "required_documents": ["RTI application form", "Fee payment proof", "Identity proof"],
    "contact_info": "Contact the PIO of the relevant public authority or visit rti.gov.in"
  }
]

QUALITY STANDARDS:
- Specificity: Be specific about authorities, processes, and requirements
- Practicality: Focus on actions the user can actually take
- Accuracy: Base recommendations on retrieved processes and legal context
- Completeness: Include all relevant details (timeline, documents, contacts)
- Clarity: Use clear, accessible language

IMPORTANT: These are informational recommendations for civic actions, NOT legal advice. Do not suggest litigation strategies."""

            user_prompt = f"""User Query: {query}

Retrieved Civic Processes:
{chr(10).join(processes_context)}

Generate 3-5 structured, actionable recommendations based on the retrieved processes. 
Focus on what the user can actually do to address their query.
Return ONLY a JSON array."""

            result = groq_llm.generate_response(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                temperature=0.3,
                max_tokens=1500
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
                recommendations = json.loads(result)
                if isinstance(recommendations, list):
                    # Validate and structure recommendations
                    structured = []
                    for rec in recommendations[:5]:
                        if isinstance(rec, dict):
                            structured.append({
                                "action": rec.get("action", "Unnamed Action"),
                                "responsible_authority": rec.get("responsible_authority", "Relevant Authority"),
                                "why_this_matters": rec.get("why_this_matters", ""),
                                "next_step": rec.get("next_step", ""),
                                "estimated_timeline": rec.get("estimated_timeline", "Varies by case"),
                                "is_legal_advice": False,
                                "sequence": len(structured) + 1
                            })
                    if structured:
                        self.logger.info(f"✓ LLM generated {len(structured)} recommendations")
                        return structured
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse LLM JSON response")
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error in LLM recommendation generation: {e}", exc_info=True)
            return []