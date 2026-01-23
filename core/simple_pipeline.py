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


def build_context(query: str) -> Dict[str, Any]:
    """
    Build context from Qdrant (RAG) and Tavily (Web Search).
    
    Returns:
        {
            "retrieved_docs": [...],
            "web_results": [...],
            "retrieval_status": "hit" | "miss"
        }
    
    NEVER blocks if retrieval is empty.
    """
    from database.qdrant_db import qdrant_manager
    from utils.embeddings import get_embedding
    from utils.tavily_search import get_tavily_search
    
    context = {
        "retrieved_docs": [],
        "web_results": [],
        "retrieval_status": "miss"
    }
    
    # Step 1: Qdrant retrieval (RAG)
    try:
        logger.info(f"📚 Retrieving from Qdrant: {query[:50]}...")
        query_embedding = get_embedding(query)
        
        # Search statutes
        statutes = qdrant_manager.search(
            collection_name="statutes_vectors",
            query_vector=query_embedding,
            limit=3,
            score_threshold=0.5
        )
        
        # Search case law
        cases = qdrant_manager.search(
            collection_name="case_law_vectors",
            query_vector=query_embedding,
            limit=3,
            score_threshold=0.5
        )
        
        # Search multimodal collection (PDFs, images, audio, video, code, forms)
        multimodal_docs = []
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            multimodal_results = qdrant_manager.client.search(
                collection_name="multimodal_legal_data",
                query_vector=query_embedding,
                limit=3,
                score_threshold=0.4
            )
            multimodal_docs = [
                {"payload": r.payload, "score": r.score}
                for r in multimodal_results
            ]
            logger.info(f"✓ Found {len(multimodal_docs)} multimodal documents")
        except Exception as e:
            logger.debug(f"Multimodal collection not available: {e}")
        
        # Combine results
        for s in statutes:
            payload = s.get("payload", {})
            context["retrieved_docs"].append({
                "type": "statute",
                "title": payload.get("title", payload.get("name", "Legal Document")),
                "content": payload.get("content", payload.get("summary", ""))[:500],
                "source": payload.get("source", "Indian Law"),
                "score": s.get("score", 0)
            })
        
        for c in cases:
            payload = c.get("payload", {})
            context["retrieved_docs"].append({
                "type": "case",
                "title": payload.get("case_name", "Court Case"),
                "content": payload.get("summary", payload.get("content", ""))[:500],
                "source": payload.get("citation", payload.get("court", "Court")),
                "score": c.get("score", 0)
            })
        
        # Add multimodal documents with data_type metadata
        for m in multimodal_docs:
            payload = m.get("payload", {})
            data_type = payload.get("data_type", "text")
            context["retrieved_docs"].append({
                "type": data_type,  # pdf, image, audio, video, code, form
                "title": payload.get("title", "Document"),
                "content": payload.get("content", "")[:500],
                "source": payload.get("source", ""),
                "category": payload.get("category", ""),
                "metadata": {k: v for k, v in payload.items() 
                           if k not in ["title", "content", "source", "data_type", "category", "id"]},
                "score": m.get("score", 0)
            })
        
        if context["retrieved_docs"]:
            context["retrieval_status"] = "hit"
            logger.info(f"✓ Retrieved {len(context['retrieved_docs'])} documents from Qdrant")
        else:
            logger.info("⚠ No documents found in Qdrant")
            
    except Exception as e:
        logger.warning(f"Qdrant retrieval error (continuing): {e}")
    
    # Step 2: Web Search (Tavily)
    try:
        logger.info(f"🌐 Searching web: {query[:50]}...")
        tavily = get_tavily_search()
        
        if tavily:
            web_results = tavily.search_legal_info(query, max_results=3)
            
            for w in web_results:
                if w.get("is_answer"):
                    # AI-generated answer from Tavily
                    context["web_results"].append({
                        "title": "Web Summary",
                        "content": w.get("content", "")[:500],
                        "url": None,
                        "is_ai_summary": True
                    })
                else:
                    context["web_results"].append({
                        "title": w.get("title", "Web Source"),
                        "content": w.get("content", "")[:400],
                        "url": w.get("url"),
                        "is_ai_summary": False
                    })
            
            if context["web_results"]:
                logger.info(f"✓ Found {len(context['web_results'])} web results")
        else:
            logger.info("⚠ Tavily not available")
            
    except Exception as e:
        logger.warning(f"Web search error (continuing): {e}")
    
    return context


def query(user_query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """
    Process a query with ONE LLM call.
    
    Pipeline:
    1. Build context (Qdrant + Tavily)
    2. Send to LLM with system prompt
    3. Return response
    
    NO multi-agent chaining. NO summarization agents.
    """
    from llm.groq_client import groq_llm
    
    try:
        logger.info(f"🚀 Simple query: {user_query[:50]}...")
        
        # Step 1: Build context
        context = build_context(user_query)
        
        # Step 2: Format context for LLM
        db_context = _format_db_context(context["retrieved_docs"])
        web_context = _format_web_context(context["web_results"])
        
        # Step 3: Build the ONE prompt
        system_prompt = """You are a helpful legal & civic information assistant for India.
You explain things clearly in simple language that anyone can understand.
You use retrieved documents and web results when provided.
If no documents are found, you still answer using general public knowledge about Indian law.
You do NOT give legal advice - only information.
You are friendly, helpful, and thorough."""

        user_prompt = f"""USER QUESTION:
{user_query}

INTERNAL DATABASE RESULTS:
{db_context if db_context else 'None found'}

WEB SEARCH RESULTS:
{web_context if web_context else 'None found'}

TASK:
1. Explain the topic simply (like a helpful assistant would)
2. If database info exists, incorporate it naturally
3. If web info exists, incorporate it naturally  
4. Clearly note when info is general knowledge vs from sources
5. Give helpful civic guidance (non-advisory)
6. End with a brief disclaimer

FORMAT YOUR RESPONSE WITH THESE SECTIONS:

### Explanation
(Clear, simple explanation of the topic)

### What the Law Says
(Legal provisions if found, or general legal framework)

### Retrieved Information
(Summary of database/web sources used, or skip if none)

### What You Can Consider
(Practical next steps - NOT legal advice)

### Disclaimer
(Brief legal disclaimer)"""

        # Step 4: ONE LLM call
        if groq_llm is None:
            logger.warning("LLM not available, returning context only")
            return _fallback_response(user_query, context)
        
        logger.info("💬 Calling LLM...")
        response = groq_llm.generate_response(
            prompt=f"{system_prompt}\n\n{user_prompt}",
            temperature=0.4,
            max_tokens=1500
        )
        
        if not response or response.strip() == "":
            logger.warning("Empty LLM response, using fallback")
            return _fallback_response(user_query, context)
        
        logger.info("✓ LLM response received")
        
        # Step 5: Build final response
        return {
            "case_id": str(uuid.uuid4()),
            "query": user_query,
            "response": response,
            "sources": {
                "database_docs": len(context["retrieved_docs"]),
                "web_results": len(context["web_results"]),
                "retrieval_status": context["retrieval_status"]
            },
            "retrieved_docs": context["retrieved_docs"][:3],
            "web_results": context["web_results"][:3],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        return {
            "case_id": str(uuid.uuid4()),
            "query": user_query,
            "response": f"I apologize, but I encountered an error processing your question. Please try again.\n\nError: {str(e)}",
            "sources": {"database_docs": 0, "web_results": 0, "retrieval_status": "error"},
            "error": str(e),
            "generated_at": datetime.now().isoformat()
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
