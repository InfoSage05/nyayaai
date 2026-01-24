"""
SIMPLIFIED PIPELINE FOR NYAYAAI

This replaces the complex multi-agent system with:
1. build_context() - Gets RAG + Web Search results
2. query() - Single LLM call with all context

NO multi-agent chaining. NO multiple LLM calls. ONE response.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# ADAPTIVE RAG HELPERS
# =============================================================================

def _analyze_query_intent(query: str) -> Dict[str, Any]:
    """
    Step 1: Lightweight Query Analysis (Heuristic).
    Determines if query needs external sources and its type.
    """
    query_lower = query.lower()
    
    # Intent Classification
    intent = "general"
    if any(k in query_lower for k in ["how to", "process", "steps", "procedure", "file", "apply"]):
        intent = "procedural"
    elif any(k in query_lower for k in ["what is", "define", "meaning", "concept", "rights", "law"]):
        intent = "informational"
        
    # Source Needs Analysis
    # (Almost all legal queries benefit from sources, but simple greetings don't)
    needs_sources = True
    if len(query.split()) < 3 and any(k in query_lower for k in ["hi", "hello", "thanks", "bye"]):
        needs_sources = False
        
    return {
        "intent": intent,
        "needs_sources": needs_sources
    }

def build_adaptive_context(query: str) -> Dict[str, Any]:
    """
    Step 2-4: Adaptive Retrieval & Context Building.
    - Vector Search (Qdrant)
    - Conditional Web Search (Tavily) if retrieval is weak
    """
    from database.qdrant_db import qdrant_manager
    from utils.tavily_search import get_tavily_search
    
    context = {
        "query": query,
        "retrieved_docs": [],
        "web_results": [],
        "context_source": "general"
    }
    
    # 1. Query Analysis
    analysis = _analyze_query_intent(query)
    context["intent"] = analysis["intent"]
    
    if not analysis["needs_sources"]:
        return context

    # 2. Vector Retrieval (Qdrant)
    try:
        from utils.embeddings import get_embedding
        
        # Generate query embedding first
        query_embedding = get_embedding(query)
        logger.info(f"📚 Searching Qdrant with embedding...")
        
        # Search existing collections
        results = []
        collections_to_try = ["multimodal_legal_data", "legal_taxonomy_vectors", "statutes_vectors", "unified_legal_vectors"]
        
        for coll in collections_to_try:
            try:
                results = qdrant_manager.search(
                    collection_name=coll,
                    query_vector=query_embedding,
                    limit=5,
                    score_threshold=0.2  # Lower threshold to get more results
                )
                if results:
                    logger.info(f"✓ Found {len(results)} docs in {coll}")
                    break
            except Exception as coll_err:
                logger.debug(f"Collection {coll} not available: {coll_err}")
                continue
             
        # Format results
        for r in results:
             payload = r.get("payload", {})
             context["retrieved_docs"].append({
                 "title": payload.get("title", payload.get("name", "Document")),
                 "content": payload.get("content", payload.get("chunk_text", payload.get("summary", "")))[:600],
                 "source": payload.get("source", payload.get("source_name", "Internal DB")),
                 "score": r.get("score", 0)
             })
        
        logger.info(f"✓ Retrieved {len(context['retrieved_docs'])} documents from Qdrant")
             
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")

    # 3. Web Search (Always run alongside DB retrieval)
    logger.info("🌐 Running Web Search...")
    try:
        tavily = get_tavily_search()
        if tavily:
            web_hits = tavily.search_legal_info(query, max_results=3)
            for w in web_hits:
                # Handle both structure types from Tavily
                if w.get("is_answer"):
                     context["web_results"].append({
                        "title": "Web Summary",
                        "content": w.get("content", "")[:500],
                        "url": None
                     })
                else:
                    context["web_results"].append({
                        "title": w.get("title", "Web Source"),
                        "content": w.get("content", "")[:500],
                        "url": w.get("url"),
                    })
            logger.info(f"✓ Found {len(context['web_results'])} web results")
    except Exception as e:
        logger.warning(f"Web search failed: {e}")
            
    # Set final source type
    if context["retrieved_docs"] and context["web_results"]:
        context["context_source"] = "hybrid"
    elif context["retrieved_docs"]:
        context["context_source"] = "database"
    elif context["web_results"]:
        context["context_source"] = "web"
        
    return context


def query(user_query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """
    Process a query with ADAPTIVE RAG (Single LLM Call).
    """
    from llm.groq_client import groq_llm
    
    try:
        logger.info(f"🚀 Adaptive Query: {user_query[:50]}...")
        
        # 1. Initialize Memory
        _init_memory_collection()
        
        # 2. Build Adaptive Context
        context = build_adaptive_context(user_query)
        
        # 3. Get Memory Context
        memory_context = _get_memory_context(user_id, user_query)
        
        # 4. Format for Prompt
        db_text = "\n\n".join([f"Source: {d['title']}\nContent: {d.get('content', '')[:600]}" for d in context["retrieved_docs"]])
        web_text = "\n\n".join([f"Source: {d['title']} ({d.get('url', 'No URL')})\nContent: {d.get('content', '')[:600]}" for d in context["web_results"]])
        
        # 5. Single LLM Generation (Adaptive RAG Prompt)
        system_prompt = """You are a helpful legal & civic information assistant.
You explain concepts clearly in simple language.
You use provided documents and web results when available.
If none are available, you rely on general public knowledge.
You do NOT provide legal advice."""

        user_prompt = f"""USER QUERY: {user_query}

INTENT: {context['intent']}

RETRIEVED DOCUMENTS (Internal DB):
{db_text if db_text else 'None retrieved (Weak match).'}

WEB SEARCH RESULTS (Adaptive Fallback):
{web_text if web_text else 'None found.'}

PAST CONVERSATION:
{memory_context if memory_context else 'None.'}

INSTRUCTIONS:
1. Analyze the Intent and Sources.
2. If sources are provided, ground your answer IN them.
3. If no sources, use general knowledge but state that clearly.
4. Explain simply and clearly.

REQUIRED OUTPUT FORMAT:

### Plain-language Explanation
(Simple, clear answer)

### What the law generally says
(Legal principles/Acts mentioned in sources or general knowledge)

### Evidence from database (if any)
(Cite specific Internal DB documents used, or state "None")

### Information from web (if any)
(Cite Web results used, or state "None")

### What you can consider
(Practical civic guidance)

### Disclaimer
(Brief legal disclaimer)"""

        # Call LLM
        if groq_llm is None:
            logger.warning("LLM not available, returning context only")
            return _fallback_response(user_query, context)
            
        logger.info("💬 Generating Adaptive Response...")
        response = groq_llm.generate_response(
            prompt=f"{system_prompt}\n\n{user_prompt}", 
            temperature=0.3
        )
        
        # Store interaction
        _store_interaction(user_id, user_query, response)
        
        return {
            "case_id": str(uuid.uuid4()),
            "query": user_query,
            "response": response,
            "sources": {
                "database_docs": len(context["retrieved_docs"]),
                "web_results": len(context["web_results"]),
                "source_type": context["context_source"],
                "retrieval_status": "hit" if context["retrieved_docs"] else "miss"
            },
            "retrieved_docs": context["retrieved_docs"][:3],
            "web_results": context["web_results"][:3],
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Pipeline Error: {e}")
        return {
             "case_id": str(uuid.uuid4()),
             "query": user_query, 
             "response": "I encountered an error processing your request.",
             "error": str(e)
        }


def _format_db_context(docs: List[Dict[str, Any]]) -> str:
    """Format database documents for LLM prompt."""
    if not docs:
        return ""
    
    lines = []
    for i, doc in enumerate(docs[:3], 1):
        lines.append(f"{i}. [{doc.get('type', 'doc').upper()}] {doc.get('title', 'Document')}")
        lines.append(f"   Source: {doc.get('source', 'Unknown')}")
        content = doc.get('content', '')
        if content:
            lines.append(f"   Content: {content[:300]}...")
        lines.append("")
    
    return "\n".join(lines)


def _format_web_context(results: List[Dict[str, Any]]) -> str:
    """Format web search results for LLM prompt."""
    if not results:
        return ""
    
    lines = []
    for i, result in enumerate(results[:3], 1):
        title = result.get('title', 'Web Source')
        if result.get('is_ai_summary'):
            lines.append(f"{i}. [AI SUMMARY] {result.get('content', '')[:400]}")
        else:
            lines.append(f"{i}. {title}")
            if result.get('url'):
                lines.append(f"   URL: {result.get('url')}")
            lines.append(f"   {result.get('content', '')[:300]}...")
        lines.append("")
    
    return "\n".join(lines)


def _fallback_response(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fallback response when LLM is unavailable."""
    response_parts = [
        "### Explanation",
        "I'm unable to generate a full response at the moment, but here's what I found:",
        ""
    ]
    
    if context["retrieved_docs"]:
        response_parts.append("### Retrieved Information")
        for doc in context["retrieved_docs"][:3]:
            response_parts.append(f"- **{doc.get('title', 'Document')}**: {doc.get('content', '')[:200]}...")
        response_parts.append("")
    
    if context["web_results"]:
        response_parts.append("### Web Information")
        for result in context["web_results"][:3]:
            response_parts.append(f"- {result.get('title', 'Source')}: {result.get('content', '')[:200]}...")
        response_parts.append("")
    
    response_parts.extend([
        "### Disclaimer",
        "This is general information only, not legal advice. Please consult a qualified lawyer for specific legal matters."
    ])
    
    return {
        "case_id": str(uuid.uuid4()),
        "query": query,
        "response": "\n".join(response_parts),
        "sources": {
            "database_docs": len(context["retrieved_docs"]),
            "web_results": len(context["web_results"]),
            "retrieval_status": context["retrieval_status"]
        },
        "retrieved_docs": context["retrieved_docs"][:3],
        "web_results": context["web_results"][:3],
        "generated_at": datetime.now().isoformat(),
        "fallback": True
    }


# =============================================================================
# MEMORY & INTERACTION HISTORY LOGIC
# =============================================================================

def _init_memory_collection():
    """Ensure user_interaction_memory collection exists."""
    from database.qdrant_db import qdrant_manager
    try:
        qdrant_manager.create_collection(
            collection_name="user_interaction_memory",
            vector_size=384
        )
    except Exception as e:
        logger.warning(f"Memory init warning: {e}")


def _store_interaction(user_id: str, query: str, response: str):
    """Store interaction in Qdrant with timestamp for long-term memory."""
    from database.qdrant_db import qdrant_manager
    from utils.embeddings import get_embedding
    from qdrant_client.models import PointStruct
    
    try:
        embedding = get_embedding(query)
        doc_id = str(uuid.uuid4())
        
        payload = {
            "user_id": user_id,
            "query": query,
            "response": response[:1000],  # Store truncated response
            "timestamp": datetime.now().isoformat(),
            "type": "interaction"
        }
        
        qdrant_manager.client.upsert(
            collection_name="user_interaction_memory",
            points=[PointStruct(
                id=doc_id,
                vector=embedding,
                payload=payload
            )]
        )
        logger.debug("✓ Stored interaction in memory")
    except Exception as e:
        logger.error(f"Error storing interaction: {e}")


def _get_memory_context(user_id: str, query: str, limit: int = 3) -> str:
    """
    Retrieve relevant past interactions for context.
    
    Implements:
    1. Relevance Search: Finds semantically similar past Q&A
    2. Recency Bias: Implicit in how LLM uses it (recent usually better)
    3. Decay: Older irrelevant memories purely filtered by vector similarity
    """
    from database.qdrant_db import qdrant_manager
    from utils.embeddings import get_embedding
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    
    try:
        embedding = get_embedding(query)
        
        # Filter by user_id
        user_filter = Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        )
        
        results = qdrant_manager.client.search(
            collection_name="user_interaction_memory",
            query_vector=embedding,
            query_filter=user_filter,
            limit=limit,
            score_threshold=0.6  # High threshold to only get relevant context
        )
        
        if not results:
            return ""
            
        memory_lines = ["Previous relevant discussions:"]
        for r in results:
            payload = r.payload
            ts = payload.get("timestamp", "")[:10]  # Just date
            memory_lines.append(f"- [{ts}] User: {payload.get('query')}")
            memory_lines.append(f"  System: {payload.get('response')[:200]}...")
            
        return "\n".join(memory_lines)
    except Exception as e:
        logger.warning(f"Memory retrieval error: {e}")
        return ""
