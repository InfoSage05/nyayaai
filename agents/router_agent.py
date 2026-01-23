"""Router Agent - Intelligently routes queries to appropriate agent pipeline."""
from typing import Dict, Any, List, Literal
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from llm.groq_client import groq_llm
import logging
import json

logger = logging.getLogger(__name__)

# Query types that determine which agents to use
QueryType = Literal[
    "legal_info",      # General legal information -> Knowledge + LLM
    "case_search",     # Looking for similar cases -> Case Similarity + LLM  
    "civic_action",    # How to file complaints, RTI, etc -> Recommendations + LLM
    "web_search",      # Need current/recent info -> Web Search + LLM
    "simple_qa"        # Simple question -> LLM only (no retrieval needed)
]


class RouterAgent(BaseAgent):
    """Routes queries to appropriate agent pipelines based on intent."""
    
    def __init__(self):
        super().__init__(
            name="router",
            description="Classifies queries and routes to appropriate agent pipeline"
        )
        
        # Keywords for fast classification (fallback)
        self.classification_keywords = {
            "legal_info": ["law", "act", "section", "article", "rights", "legal", "constitution", "ipc", "crpc"],
            "case_search": ["case", "judgment", "verdict", "court", "precedent", "similar", "ruling"],
            "civic_action": ["file", "complaint", "rti", "application", "how to", "procedure", "steps", "process", "lodge", "register"],
            "web_search": ["latest", "recent", "current", "news", "update", "2024", "2025", "2026"],
            "simple_qa": ["what is", "define", "meaning", "explain", "who is"]
        }
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Classify query and determine agent pipeline.
        
        Args:
            input_data: User query
            
        Returns:
            Classification result with recommended pipeline
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result={"query_type": "simple_qa", "agents": ["llm"]},
                confidence=0.5,
                reasoning="Invalid input, defaulting to simple QA",
                agent_name=self.name
            )
        
        query = input_data.query.lower().strip()
        
        # Step 1: Try LLM-based classification for accuracy
        self.logger.info("Attempting LLM-based query classification...")
        llm_result = self._llm_classify(input_data.query)
        
        if llm_result.get("success"):
            query_type = llm_result.get("query_type", "legal_info")
            confidence = 0.9
            method = "llm"
        else:
            # Step 2: Fallback to keyword-based classification
            self.logger.info("Using keyword-based classification fallback...")
            query_type = self._keyword_classify(query)
            confidence = 0.7
            method = "keyword"
        
        # Determine agent pipeline based on query type
        pipeline = self._get_pipeline(query_type)
        
        return AgentOutput(
            result={
                "query_type": query_type,
                "agents": pipeline["agents"],
                "description": pipeline["description"],
                "skip_agents": pipeline["skip"]
            },
            confidence=confidence,
            reasoning=f"Classified as '{query_type}' using {method} method. Pipeline: {pipeline['agents']}",
            agent_name=self.name,
            metadata={
                "classification_method": method,
                "query_type": query_type,
                "pipeline_length": len(pipeline["agents"])
            }
        )
    
    def _llm_classify(self, query: str) -> Dict[str, Any]:
        """Use LLM to classify query type."""
        if groq_llm is None:
            return {"success": False}
        
        try:
            prompt = f"""Classify this legal query into ONE category:

Query: "{query}"

Categories:
1. legal_info - General legal information, laws, acts, rights, sections
2. case_search - Looking for court cases, judgments, precedents
3. civic_action - How to file complaints, RTI, applications, procedures
4. web_search - Needs current/recent information, news, updates
5. simple_qa - Simple definition or explanation question

Return ONLY a JSON object:
{{"query_type": "category_name", "reason": "brief reason"}}"""

            result = groq_llm.generate_response(
                prompt=prompt,
                temperature=0.1,
                max_tokens=100
            )
            
            if not result:
                return {"success": False}
            
            # Parse JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
                result = result.strip()
            
            parsed = json.loads(result)
            if isinstance(parsed, dict) and "query_type" in parsed:
                valid_types = ["legal_info", "case_search", "civic_action", "web_search", "simple_qa"]
                if parsed["query_type"] in valid_types:
                    self.logger.info(f"✓ LLM classified as: {parsed['query_type']}")
                    return {"success": True, "query_type": parsed["query_type"]}
            
            return {"success": False}
            
        except Exception as e:
            self.logger.warning(f"LLM classification failed: {e}")
            return {"success": False}
    
    def _keyword_classify(self, query: str) -> str:
        """Classify query using keyword matching."""
        scores = {qtype: 0 for qtype in self.classification_keywords}
        
        for qtype, keywords in self.classification_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    scores[qtype] += 1
        
        # Return highest scoring type, default to legal_info
        best_type = max(scores, key=scores.get)
        if scores[best_type] == 0:
            return "legal_info"  # Default
        
        return best_type
    
    def _get_pipeline(self, query_type: str) -> Dict[str, Any]:
        """Get agent pipeline configuration for query type."""
        pipelines = {
            "legal_info": {
                "agents": ["intake", "classification", "knowledge_retrieval", "reasoning", "summarization"],
                "skip": ["case_similarity", "web_search", "recommendation"],
                "description": "Legal information retrieval with statute search"
            },
            "case_search": {
                "agents": ["intake", "classification", "case_similarity", "reasoning", "summarization"],
                "skip": ["knowledge_retrieval", "web_search", "recommendation"],
                "description": "Case law search and analysis"
            },
            "civic_action": {
                "agents": ["intake", "classification", "knowledge_retrieval", "recommendation", "summarization"],
                "skip": ["case_similarity", "web_search", "reasoning"],
                "description": "Civic action procedures and recommendations"
            },
            "web_search": {
                "agents": ["intake", "classification", "web_search", "reasoning", "summarization"],
                "skip": ["knowledge_retrieval", "case_similarity", "recommendation"],
                "description": "Current information from web sources"
            },
            "simple_qa": {
                "agents": ["intake", "reasoning", "summarization"],
                "skip": ["classification", "knowledge_retrieval", "case_similarity", "web_search", "recommendation"],
                "description": "Direct LLM response for simple questions"
            }
        }
        
        return pipelines.get(query_type, pipelines["legal_info"])
