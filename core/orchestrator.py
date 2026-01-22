"""Multi-agent orchestrator using LangGraph."""
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
import logging
from core.agent_base import AgentInput, AgentOutput
from agents.intake_agent import IntakeAgent
from agents.classification_agent import ClassificationAgent
from agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.case_similarity_agent import CaseSimilarityAgent
from agents.reasoning_agent import ReasoningAgent
from agents.recommendation_agent import RecommendationAgent
from agents.ethics_agent import EthicsAgent
from agents.memory_agent import MemoryAgent
from agents.summarization_agent import SummarizationAgent

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State passed between agents."""
    query: str
    context: Dict[str, Any]
    agent_outputs: Dict[str, AgentOutput]
    final_result: Dict[str, Any]
    errors: list


class NyayaOrchestrator:
    """Orchestrates multi-agent workflow."""
    
    def __init__(self):
        """Initialize orchestrator with all agents."""
        try:
            self.intake_agent = IntakeAgent()
            self.classification_agent = ClassificationAgent()
            self.knowledge_agent = KnowledgeRetrievalAgent()
            self.case_agent = CaseSimilarityAgent()
            self.reasoning_agent = ReasoningAgent()
            self.recommendation_agent = RecommendationAgent()
            self.ethics_agent = EthicsAgent()
            self.memory_agent = MemoryAgent()
            self.summarization_agent = SummarizationAgent()
            
            # Build graph
            self.graph = self._build_graph()
            self.app = self.graph.compile()
        except Exception as e:
            logger.error(f"Error initializing orchestrator: {e}", exc_info=True)
            raise
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("intake", self._intake_node)
        workflow.add_node("classification", self._classification_node)
        workflow.add_node("knowledge_retrieval", self._knowledge_node)
        workflow.add_node("case_similarity", self._case_node)
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("recommendation", self._recommendation_node)
        workflow.add_node("ethics", self._ethics_node)
        workflow.add_node("memory", self._memory_node)
        workflow.add_node("summarization", self._summarization_node)
        
        # Define edges
        workflow.set_entry_point("intake")
        workflow.add_edge("intake", "classification")
        workflow.add_edge("classification", "knowledge_retrieval")
        workflow.add_edge("knowledge_retrieval", "case_similarity")
        workflow.add_edge("case_similarity", "reasoning")
        workflow.add_edge("reasoning", "recommendation")
        workflow.add_edge("recommendation", "ethics")
        workflow.add_edge("ethics", "memory")
        workflow.add_edge("memory", "summarization")
        workflow.add_edge("summarization", END)
        
        return workflow
    
    def _intake_node(self, state: AgentState) -> AgentState:
        """Intake agent node."""
        try:
            input_data = AgentInput(query=state["query"])
            output = self.intake_agent.process(input_data)
            
            # Update context with normalized query and embedding
            state["context"]["normalized_query"] = output.result.get("normalized_query")
            state["context"]["embedding"] = output.result.get("embedding")
            state["agent_outputs"]["intake"] = output
        except Exception as e:
            logger.error(f"Error in intake node: {e}")
            state["errors"].append(f"Intake error: {str(e)}")
        return state
    
    def _classification_node(self, state: AgentState) -> AgentState:
        """Classification agent node."""
        try:
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.classification_agent.process(input_data)
            
            # Update context with domains
            state["context"]["domains"] = output.result.get("domains", [])
            state["context"]["primary_domain"] = output.result.get("primary_domain", "general")
            state["agent_outputs"]["classification"] = output
        except Exception as e:
            logger.error(f"Error in classification node: {e}")
            state["errors"].append(f"Classification error: {str(e)}")
        return state
    
    def _knowledge_node(self, state: AgentState) -> AgentState:
        """Knowledge retrieval agent node."""
        try:
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.knowledge_agent.process(input_data)
            
            # Update context with statutes
            state["context"]["statutes"] = output.result.get("statutes", [])
            state["agent_outputs"]["knowledge"] = output
        except Exception as e:
            logger.error(f"Error in knowledge node: {e}")
            state["errors"].append(f"Knowledge retrieval error: {str(e)}")
        return state
    
    def _case_node(self, state: AgentState) -> AgentState:
        """Case similarity agent node."""
        try:
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.case_agent.process(input_data)
            
            # Update context with cases
            state["context"]["similar_cases"] = output.result.get("similar_cases", [])
            state["agent_outputs"]["case_similarity"] = output
        except Exception as e:
            logger.error(f"Error in case node: {e}")
            state["errors"].append(f"Case similarity error: {str(e)}")
        return state
    
    def _reasoning_node(self, state: AgentState) -> AgentState:
        """Reasoning agent node."""
        try:
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.reasoning_agent.process(input_data)
            
            # Update context with explanation
            explanation = output.result.get("explanation", "") if output.result else ""
            
            # Ensure explanation is never empty
            if not explanation or explanation.strip() == "":
                statutes_count = len(state["context"].get("statutes", []))
                cases_count = len(state["context"].get("similar_cases", []))
                explanation = f"Based on {statutes_count} retrieved statutes and {cases_count} similar cases, here are the relevant legal provisions."
            
            state["context"]["explanation"] = explanation
            state["agent_outputs"]["reasoning"] = output
        except Exception as e:
            logger.error(f"Error in reasoning node: {e}")
            state["errors"].append(f"Reasoning error: {str(e)}")
            # Provide fallback explanation
            state["context"]["explanation"] = "Legal provisions apply to your query. Please review the statutes and cases above for details."
        return state
    
    def _recommendation_node(self, state: AgentState) -> AgentState:
        """Recommendation agent node."""
        try:
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.recommendation_agent.process(input_data)
            
            # Update context with recommendations
            state["context"]["recommendations"] = output.result.get("recommendations", [])
            state["agent_outputs"]["recommendation"] = output
        except Exception as e:
            logger.error(f"Error in recommendation node: {e}")
            state["errors"].append(f"Recommendation error: {str(e)}")
        return state
    
    def _ethics_node(self, state: AgentState) -> AgentState:
        """Ethics agent node."""
        try:
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.ethics_agent.process(input_data)
            
            # Update context with ethics validation
            state["context"]["ethics_check"] = output.result
            state["agent_outputs"]["ethics"] = output
        except Exception as e:
            logger.error(f"Error in ethics node: {e}")
            state["errors"].append(f"Ethics error: {str(e)}")
        return state
    
    def _memory_node(self, state: AgentState) -> AgentState:
        """Memory agent node."""
        try:
            # Store memory
            state["context"]["memory_operation"] = "store"
            input_data = AgentInput(
                query=state["query"],
                context=state["context"]
            )
            output = self.memory_agent.process(input_data)
            
            state["agent_outputs"]["memory"] = output
            
            # Pass agent_outputs to context for summarization agent
            state["context"]["agent_outputs"] = state["agent_outputs"]
        except Exception as e:
            logger.error(f"Error in memory node: {e}")
            state["errors"].append(f"Memory error: {str(e)}")
        return state
    
    def _summarization_node(self, state: AgentState) -> AgentState:
        """Summarization agent node - generates unified final response."""
        try:
            # Prepare input for summarization agent
            input_data = AgentInput(
                query=state["query"],
                context={
                    **state["context"],
                    "agent_outputs": state["agent_outputs"]
                }
            )
            output = self.summarization_agent.process(input_data)
            
            state["agent_outputs"]["summarization"] = output
            
            # Use summarization result as final result
            if output.result:
                state["final_result"] = output.result
                # Ensure case_id is included
                if "case_id" not in state["final_result"]:
                    memory_output = state["agent_outputs"].get("memory")
                    if memory_output and hasattr(memory_output, "result") and memory_output.result:
                        state["final_result"]["case_id"] = memory_output.result.get("case_id")
            else:
                # Fallback if summarization failed
                explanation = state["context"].get("explanation", "") or "Unable to generate explanation."
                state["final_result"] = {
                    "query": state["query"],
                    "unified_summary": explanation,
                    "normalized_query": state["context"].get("normalized_query"),
                    "domains": state["context"].get("domains", []),
                    "statutes": state["context"].get("statutes", []),
                    "similar_cases": state["context"].get("similar_cases", []),
                    "recommendations": state["context"].get("recommendations", []),
                    "retrieval_evidence": {
                        "statutes_count": len(state["context"].get("statutes", [])),
                        "cases_count": len(state["context"].get("similar_cases", [])),
                        "recommendations_count": len(state["context"].get("recommendations", []))
                    }
                }
        except Exception as e:
            logger.error(f"Error in summarization node: {e}")
            state["errors"].append(f"Summarization error: {str(e)}")
            # Fallback final result
            state["final_result"] = {
                "query": state["query"],
                "unified_summary": "Error generating unified response. Please try again.",
                "error": str(e)
            }
        return state
    
    def process_query(self, query: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """Process a user query through the agent pipeline.
        
        Args:
            query: User query string
            user_id: Optional user identifier
            
        Returns:
            Final result dictionary
        """
        initial_state: AgentState = {
            "query": query,
            "context": {"user_id": user_id},
            "agent_outputs": {},
            "final_result": {},
            "errors": []
        }
        
        try:
            final_state = self.app.invoke(initial_state)
            return final_state["final_result"]
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "query": query,
                "error": str(e),
                "errors": initial_state.get("errors", [])
            }

    def process_query_structured(self, query: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """NEW: Process query and return structured multi-perspective response.
        
        This is the PRIMARY method for refactored NyayaAI.
        It orchestrates all agents and synthesizes a unified response.
        
        Returns:
            StructuredQueryResponse with:
            - llm_reasoned_answer
            - retrieved_evidence  
            - similar_case_analysis
            - civic_action_recommendations
            - agent_trace
        """
        from llm.groq_client import groq_llm
        from api.schemas import (
            StructuredQueryResponse, LLMReasonedAnswer, RetrievedEvidence,
            Statute, Case, SimilarCaseAnalysis, CivicRecommendation, AgentTrace
        )
        from datetime import datetime
        import uuid
        
        try:
            # Phase 1: Run agent pipeline
            initial_state: AgentState = {
                "query": query,
                "context": {"user_id": user_id},
                "agent_outputs": {},
                "final_result": {},
                "errors": []
            }
            
            logger.info(f"Starting structured query processing: {query[:50]}...")
            final_state = self.app.invoke(initial_state)
            
            # Phase 2: Extract agent outputs
            agents_output = final_state.get("agent_outputs", {})
            context = final_state.get("context", {})
            
            # Phase 3: Build evidence objects
            statutes_data = context.get("statutes", [])
            statutes = [
                Statute(
                    title=s.get("title", s.get("name", "Unknown Statute")),
                    summary=s.get("summary", s.get("content", "")[:300]),
                    source=s.get("source", "Unknown"),
                    relevance_score=s.get("score")
                )
                for s in statutes_data[:5]
            ]
            
            # Pipeline stores similar cases under `similar_cases` (legacy key `cases` may be absent)
            cases_data = context.get("similar_cases", []) or context.get("cases", [])
            cases = [
                Case(
                    case_name=c.get("case_name", "Unknown Case"),
                    year=c.get("year"),
                    summary=c.get("summary", c.get("outcome", "")[:300]),
                    source=c.get("source", c.get("citation", "Unknown")),
                    relevance_score=c.get("score")
                )
                for c in cases_data[:5]
            ]
            
            retrieved_evidence = RetrievedEvidence(
                statutes=statutes,
                cases=cases,
                total_evidence_count=len(statutes) + len(cases)
            )
            
            # Phase 4: Call LLM for synthesis (CRITICAL - single point of LLM call)
            # If Groq isn't installed/configured, fall back to retrieval-only output.
            if groq_llm is None:
                explanation = context.get("explanation") or "Unable to synthesize response (LLM unavailable)."
                llm_answer = {
                    "summary": explanation[:500],
                    "confidence_level": "low",
                    "reasoning_steps": [
                        "LLM synthesis unavailable; returning retrieval-grounded summary only."
                    ],
                    "limitations": "Groq LLM not configured/installed; no synthesis performed.",
                    "disclaimers": [
                        "This system provides legal information only, not legal advice."
                    ],
                }
            else:
                llm_answer = groq_llm.synthesize_legal_answer(
                    query=query,
                    retrieved_statutes=[{
                        "title": s.title,
                        "summary": s.summary,
                        "source": s.source
                    } for s in statutes],
                    similar_cases=[{
                        "case_name": c.case_name,
                        "summary": c.summary,
                        "source": c.source
                    } for c in cases],
                    temperature=0.3,
                    max_tokens=2000
                )
            
            llm_reasoned_answer = LLMReasonedAnswer(
                summary=llm_answer.get("summary", "Unable to synthesize response"),
                confidence_level=llm_answer.get("confidence_level", "medium"),
                reasoning_steps=llm_answer.get("reasoning_steps", []),
                limitations=llm_answer.get("limitations", ""),
                disclaimers=llm_answer.get("disclaimers", [])
            )
            
            # Phase 5: Extract similar case analysis
            similar_cases_raw = context.get("similar_cases", [])
            similar_case_analysis = [
                SimilarCaseAnalysis(
                    case_context=c.get("case_context", ""),
                    what_happened=c.get("what_happened", ""),
                    outcome=c.get("outcome", ""),
                    relevance_to_query=c.get("relevance_to_query", ""),
                    source=c.get("source")
                )
                for c in similar_cases_raw[:5]
                if isinstance(c, dict)  # Ensure it's structured
            ]
            
            # Phase 6: Extract civic recommendations
            recommendations_raw = context.get("recommendations", [])
            civic_recommendations = [
                CivicRecommendation(
                    action=r.get("action", "Unnamed Action"),
                    responsible_authority=r.get("responsible_authority", r.get("authority", "")),
                    why_this_matters=r.get("why_this_matters", ""),
                    next_step=r.get("next_step", ""),
                    estimated_timeline=r.get("estimated_timeline"),
                    is_legal_advice=r.get("is_legal_advice", False)
                )
                for r in recommendations_raw[:5]
                if isinstance(r, dict)  # Ensure it's structured
            ]
            
            # Phase 7: Build agent trace for transparency
            agent_trace = AgentTrace(
                classification_domain=context.get("primary_domain", "general"),
                retrieval_summary=f"Retrieved {len(statutes)} statutes, {len(cases)} cases",
                case_analysis_summary=f"Analyzed {len(similar_case_analysis)} similar cases",
                recommendation_count=len(civic_recommendations)
            )
            
            # Phase 8: Assemble final structured response
            response = StructuredQueryResponse(
                case_id=str(uuid.uuid4()),
                query=query,
                legal_domain=context.get("primary_domain", "general"),
                llm_reasoned_answer=llm_reasoned_answer,
                retrieved_evidence=retrieved_evidence,
                similar_case_analysis=similar_case_analysis,
                civic_action_recommendations=civic_recommendations,
                agent_trace=agent_trace,
                generated_at=datetime.now().isoformat()
            )
            
            logger.info(f"✓ Structured response generated for case {response.case_id}")
            return response.model_dump()
        
        except Exception as e:
            logger.error(f"Error in structured query processing: {e}", exc_info=True)
            # Return minimal valid response
            return {
                "case_id": str(uuid.uuid4()),
                "query": query,
                "legal_domain": "general",
                "llm_reasoned_answer": {
                    "summary": f"Error processing query: {str(e)}",
                    "confidence_level": "low",
                    "reasoning_steps": [],
                    "limitations": "Error occurred during processing",
                    "disclaimers": ["System error - please try again"]
                },
                "retrieved_evidence": {"statutes": [], "cases": [], "total_evidence_count": 0},
                "similar_case_analysis": [],
                "civic_action_recommendations": [],
                "agent_trace": {
                    "classification_domain": "general",
                    "retrieval_summary": "Error",
                    "case_analysis_summary": "Error",
                    "recommendation_count": 0
                }
            }


# Global orchestrator instance - lazy initialization to prevent crashes on import
_orchestrator_instance = None

def get_orchestrator() -> NyayaOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        try:
            _orchestrator_instance = NyayaOrchestrator()
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
            raise
    return _orchestrator_instance

# For backward compatibility - lazy initialization to prevent crashes
# Don't initialize at import time - wait until first API call
orchestrator = None

def _init_orchestrator():
    """Initialize orchestrator on first use (called from API endpoints)."""
    global orchestrator
    if orchestrator is None:
        orchestrator = get_orchestrator()
    return orchestrator
