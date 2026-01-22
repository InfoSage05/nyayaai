"""Pydantic schemas for API."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class QueryRequest(BaseModel):
    """Request schema for query endpoint."""
    query: str = Field(..., description="User legal query")
    user_id: Optional[str] = Field(None, description="Optional user identifier")


# ============================================================================
# NEW STRUCTURED RESPONSE SCHEMA
# ============================================================================

class LLMReasonedAnswer(BaseModel):
    """LLM synthesis of the query with evidence."""
    summary: str = Field(..., description="Main synthesized answer")
    confidence_level: Literal["low", "medium", "high"] = "medium"
    reasoning_steps: List[str] = []
    limitations: str = ""
    disclaimers: List[str] = []


class Statute(BaseModel):
    """Retrieved statute/act."""
    title: str
    summary: str
    source: str
    relevance_score: Optional[float] = None


class Case(BaseModel):
    """Retrieved case law."""
    case_name: str
    year: Optional[int] = None
    summary: str
    source: str
    relevance_score: Optional[float] = None


class RetrievedEvidence(BaseModel):
    """All retrieved legal evidence."""
    statutes: List[Statute] = []
    cases: List[Case] = []
    total_evidence_count: int = 0


class SimilarCaseAnalysis(BaseModel):
    """Analysis of a similar past case."""
    case_context: str = Field(..., description="What was the issue about?")
    what_happened: str = Field(..., description="What actions were taken?")
    outcome: str = Field(..., description="What was the result?")
    relevance_to_query: str = Field(..., description="Why this case matters for your query")
    source: Optional[str] = None


class CivicRecommendation(BaseModel):
    """Structured civic action recommendation."""
    action: str = Field(..., description="What to do")
    responsible_authority: str = Field(..., description="Which authority handles this")
    why_this_matters: str = Field(..., description="Impact of this action")
    next_step: str = Field(..., description="Concrete next action")
    estimated_timeline: Optional[str] = None
    is_legal_advice: bool = False


class AgentTrace(BaseModel):
    """Transparent trace of agent outputs."""
    classification_domain: str = ""
    retrieval_summary: str = ""
    case_analysis_summary: str = ""
    recommendation_count: int = 0


class StructuredQueryResponse(BaseModel):
    """New unified response structure."""
    case_id: str
    query: str
    legal_domain: str

    llm_reasoned_answer: LLMReasonedAnswer
    retrieved_evidence: RetrievedEvidence
    similar_case_analysis: List[SimilarCaseAnalysis] = []
    civic_action_recommendations: List[CivicRecommendation] = []

    agent_trace: AgentTrace
    generated_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "CASE_001",
                "query": "How do I file an RTI application?",
                "legal_domain": "Information Rights",
                "llm_reasoned_answer": {
                    "summary": "You can file an RTI request with any public authority...",
                    "confidence_level": "high",
                    "reasoning_steps": ["Identify authority", "Prepare application"],
                    "limitations": "This is general information only"
                }
            }
        }


# BACKWARD COMPATIBILITY - Keep old schema for gradual migration
class QueryResponse(BaseModel):
    """Response schema for query endpoint (legacy)."""
    query: str
    normalized_query: Optional[str] = None
    domains: List[str] = []
    explanation: str
    statutes: List[Dict[str, Any]] = []
    cases: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    ethics_check: Dict[str, Any] = {}
    case_id: Optional[str] = None
    retrieval_evidence: Dict[str, int] = {}
    disclaimers: Dict[str, str] = {}
    error: Optional[str] = None
    errors: List[str] = []


class MemoryRequest(BaseModel):
    """Request schema for memory retrieval."""
    case_id: Optional[str] = Field(None, description="Specific case ID to retrieve")
    query: Optional[str] = Field(None, description="Query to find similar cases")


class MemoryResponse(BaseModel):
    """Response schema for memory endpoint."""
    memories: List[Dict[str, Any]] = []
    count: int = 0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    qdrant_connected: bool
