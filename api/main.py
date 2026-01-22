"""FastAPI main application."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from config.settings import settings
# Orchestrator is initialized lazily via _init_orchestrator() in endpoints
from database.qdrant_client import qdrant_manager
from api.schemas import (
    QueryRequest, QueryResponse, MemoryRequest, MemoryResponse, 
    HealthResponse, StructuredQueryResponse
)

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agent Legal Rights & Civic Access System"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check Qdrant connection
        collections = qdrant_manager.client.get_collections()
        qdrant_connected = True
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        qdrant_connected = False
    
    return HealthResponse(
        status="healthy" if qdrant_connected else "degraded",
        version=settings.app_version,
        qdrant_connected=qdrant_connected
    )


@app.post("/api/v1/query/structured", response_model=StructuredQueryResponse, tags=["Query"])
async def process_query_structured(request: QueryRequest):
    """NEW: Process query with structured multi-perspective response.
    
    Returns organized response with:
    - Legal reasoning (LLM synthesis)
    - Evidence used (statutes + cases)
    - Similar case analysis
    - Civic action recommendations
    - Agent trace (for transparency)
    
    This is the PRIMARY endpoint for refactored NyayaAI.
    """
    try:
        logger.info(f"Processing structured query: {request.query[:100]}...")
        
        # Ensure orchestrator is initialized
        from core.orchestrator import _init_orchestrator
        global orchestrator
        orchestrator = _init_orchestrator()
        
        result = orchestrator.process_query_structured(
            query=request.query,
            user_id=request.user_id or "anonymous"
        )
        
        return StructuredQueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Error processing structured query: {e}", exc_info=True)
        # Return error response
        from datetime import datetime
        import uuid
        return StructuredQueryResponse(
            case_id=str(uuid.uuid4()),
            query=request.query,
            legal_domain="error",
            llm_reasoned_answer={
                "summary": f"Error: {str(e)}",
                "confidence_level": "low",
                "reasoning_steps": [],
                "limitations": "System error occurred",
                "disclaimers": ["Please try again"]
            },
            retrieved_evidence={"statutes": [], "cases": [], "total_evidence_count": 0},
            similar_case_analysis=[],
            civic_action_recommendations=[],
            agent_trace={
                "classification_domain": "error",
                "retrieval_summary": "Failed",
                "case_analysis_summary": "Failed",
                "recommendation_count": 0
            },
            generated_at=datetime.now().isoformat()
        )


@app.post("/api/v1/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: QueryRequest):
    """LEGACY: Process a legal query through the multi-agent system.
    
    Args:
        request: Query request with user query
        
    Returns:
        Query response with legal information and recommendations
        
    Note: Use /api/v1/query/structured for new structured response format.
    """
    try:
        logger.info(f"Processing query (legacy): {request.query[:100]}...")
        
        # Ensure orchestrator is initialized
        from core.orchestrator import _init_orchestrator
        global orchestrator
        orchestrator = _init_orchestrator()
        
        result = orchestrator.process_query(
            query=request.query,
            user_id=request.user_id or "anonymous"
        )
        
        # If there's an error in result, convert to API error response
        if "error" in result:
            logger.error(f"Orchestrator returned error: {result['error']}")
            # Still return valid response but with error field
            return QueryResponse(
                query=request.query,
                explanation="An error occurred processing your query. Please try again.",
                error=result.get("error")
            )
        
        return QueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        # Return valid response instead of raising exception
        return QueryResponse(
            query=request.query,
            explanation="An unexpected error occurred. Please try again.",
            error=str(e)
        )


@app.get("/api/v1/memory/{case_id}", response_model=MemoryResponse, tags=["Memory"])
async def get_memory(case_id: str):
    """Retrieve case memory by ID.
    
    Args:
        case_id: Case ID to retrieve
        
    Returns:
        Memory response with case information
    """
    try:
        from agents.memory_agent import MemoryAgent
        from core.agent_base import AgentInput
        
        memory_agent = MemoryAgent()
        input_data = AgentInput(
            query="",
            context={"case_id": case_id, "memory_operation": "retrieve"}
        )
        output = memory_agent.process(input_data)
        
        return MemoryResponse(
            memories=output.result.get("memories", []),
            count=output.result.get("count", 0)
        )
    
    except Exception as e:
        logger.error(f"Error retrieving memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory/search", response_model=MemoryResponse, tags=["Memory"])
async def search_memory(request: MemoryRequest):
    """Search for similar cases in memory.
    
    Args:
        request: Memory search request
        
    Returns:
        Memory response with similar cases
    """
    try:
        from agents.memory_agent import MemoryAgent
        from core.agent_base import AgentInput
        
        memory_agent = MemoryAgent()
        input_data = AgentInput(
            query=request.query or "",
            context={"memory_operation": "retrieve"}
        )
        output = memory_agent.process(input_data)
        
        return MemoryResponse(
            memories=output.result.get("memories", []),
            count=output.result.get("count", 0)
        )
    
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
