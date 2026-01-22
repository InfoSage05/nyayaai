"""Unified response schema for NyayaAI."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class StatuteSummary(BaseModel):
    """Summary of a retrieved statute."""
    title: str
    summary: str
    source: str
    section: Optional[str] = None
    act_name: Optional[str] = None
    relevance_score: float = 0.0


class CaseSummary(BaseModel):
    """Summary of a retrieved case."""
    case_name: str
    year: Optional[int] = None
    summary: str
    court: Optional[str] = None
    citation: Optional[str] = None
    relevance_score: float = 0.0


class RetrievedEvidence(BaseModel):
    """Retrieved evidence from legal corpus."""
    statutes: List[StatuteSummary] = []
    cases: List[CaseSummary] = []


class SimilarCaseAnalysis(BaseModel):
    """Analysis of a similar past case."""
    context: str = Field(..., description="What was the context/issue?")
    what_happened: str = Field(..., description="What action was taken?")
    outcome: str = Field(..., description="What was the outcome?")
    relevance: str = Field(..., description="Why is this relevant to the query?")
    case_name: str
    year: Optional[int] = None


class CivicActionRecommendation(BaseModel):
    """Structured civic action recommendation."""
    action: str = Field(..., description="What action to take")
    authority: str = Field(..., description="Which authority handles this")
    why: str = Field(..., description="Why this action matters")
    next_step: str = Field(..., description="What happens next")
    timeline: Optional[str] = None
    cost: Optional[str] = None


class LLMReasonedAnswer(BaseModel):
    """LLM-generated reasoned answer."""
    summary: str = Field(..., description="Coherent explanation of the issue")
    confidence_level: Literal["low", "medium", "high"] = "medium"
    limitations: str = Field(..., description="What is unknown or unclear")
    key_points: List[str] = Field(default_factory=list, description="Key points from reasoning")


class AgentTrace(BaseModel):
    """Trace of agent outputs for transparency."""
    classification_agent: str = Field(..., description="Domain classification reasoning")
    retrieval_agent: str = Field(..., description="Retrieval strategy and results")
    reasoning_agent: str = Field(..., description="Reasoning process")
    recommendation_agent: str = Field(..., description="Recommendation logic")
    case_similarity_agent: str = Field(..., description="Case similarity analysis")


class NyayaAIResponse(BaseModel):
    """Unified response schema for NyayaAI."""
    case_id: str
    query: str
    normalized_query: Optional[str] = None
    legal_domain: str
    
    llm_reasoned_answer: LLMReasonedAnswer
    
    retrieved_evidence: RetrievedEvidence
    
    similar_case_analysis: List[SimilarCaseAnalysis] = []
    
    civic_action_recommendations: List[CivicActionRecommendation] = []
    
    agent_trace: AgentTrace
    
    metadata: dict = Field(default_factory=dict)
