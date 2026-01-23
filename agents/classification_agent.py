"""Legal Domain Classification Agent - Classifies queries into legal domains."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_db import qdrant_manager
from utils.embeddings import get_embedding
from llm.groq_client import groq_llm
import json
import logging

logger = logging.getLogger(__name__)

# Legal domain taxonomy
LEGAL_DOMAINS = [
    "constitutional_law",
    "criminal_law",
    "civil_law",
    "family_law",
    "property_law",
    "labor_law",
    "consumer_protection",
    "environmental_law",
    "tax_law",
    "corporate_law",
    "intellectual_property",
    "administrative_law",
    "civic_rights",
    "human_rights"
]


class ClassificationAgent(BaseAgent):
    """Classifies legal queries into specific domains."""
    
    def __init__(self):
        super().__init__(
            name="legal_domain_classification",
            description="Classifies user queries into legal domains using taxonomy search"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Classify query into legal domain.
        
        Args:
            input_data: Normalized query with embedding
            
        Returns:
            Classification result with domain(s)
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input",
                agent_name=self.name
            )
        
        # Step 1: Try LLM-based classification first
        self.logger.info("Attempting LLM-based classification...")
        classified_domains = self._llm_classify(input_data.query)
        classification_method = "llm"
        results = []
        confidence = 0.5
        
        # Step 2: If LLM fails, try taxonomy search
        if not classified_domains:
            self.logger.info("LLM classification failed, trying taxonomy search...")
            context = input_data.context or {}
            if "embedding" in context:
                query_embedding = context["embedding"]
            else:
                query_embedding = get_embedding(input_data.query)
            
            results = qdrant_manager.search(
                collection_name="legal_taxonomy_vectors",
                query_vector=query_embedding,
                limit=3,
                score_threshold=0.4
            )
            
            self.log_retrieval("legal_taxonomy_vectors", len(results), 0.4)
            
            # Extract domains from retrieved taxonomy
            if results:
                for result in results:
                    domain = result["payload"].get("domain", "")
                    if domain and domain not in classified_domains:
                        classified_domains.append(domain)
                classification_method = "taxonomy"
                confidence = results[0]["score"] if results else 0.5
        
        # Step 3: Final fallback to keyword matching
        if not classified_domains:
            self.logger.info("Taxonomy search failed, using keyword matching fallback...")
            classified_domains = self._keyword_classify(input_data.query)
            classification_method = "keyword"
            confidence = 0.5
        
        # If LLM was used, set higher confidence
        if classification_method == "llm":
            confidence = 0.85
        
        return AgentOutput(
            result={
                "domains": classified_domains,
                "primary_domain": classified_domains[0] if classified_domains else "general"
            },
            retrieved_documents=results,
            confidence=float(confidence),
            reasoning=f"Classified into {len(classified_domains)} domain(s) using {classification_method}",
            agent_name=self.name,
            metadata={
                "classification_method": classification_method,
                "llm_used": classification_method == "llm",
                "fallback_used": classification_method in ["taxonomy", "keyword"]
            }
        )
    
    def _keyword_classify(self, query: str) -> List[str]:
        """Fallback keyword-based classification."""
        query_lower = query.lower()
        matched_domains = []
        
        keyword_map = {
            "constitutional_law": ["constitution", "fundamental right", "article"],
            "criminal_law": ["crime", "criminal", "arrest", "bail", "fir", "police"],
            "civil_law": ["contract", "tort", "damages", "compensation"],
            "family_law": ["marriage", "divorce", "custody", "maintenance", "adoption"],
            "property_law": ["property", "land", "ownership", "title", "possession"],
            "labor_law": ["employment", "wage", "termination", "labor", "worker"],
            "consumer_protection": ["consumer", "defective", "refund", "warranty"],
            "environmental_law": ["environment", "pollution", "forest", "wildlife"],
            "tax_law": ["tax", "income tax", "gst", "assessment"],
            "corporate_law": ["company", "corporate", "shareholder", "board"],
            "intellectual_property": ["patent", "copyright", "trademark", "ip"],
            "administrative_law": ["government", "public authority", "administrative"],
            "civic_rights": ["voting", "citizen", "civic", "right to information"],
            "human_rights": ["human right", "discrimination", "equality"]
        }
        
        for domain, keywords in keyword_map.items():
            if any(keyword in query_lower for keyword in keywords):
                matched_domains.append(domain)
        
        return matched_domains[:3]  # Return top 3 matches
    
    def _llm_classify(self, query: str) -> List[str]:
        """Use LLM to classify query into legal domains.
        
        Args:
            query: User query string
            
        Returns:
            List of classified domain names
        """
        if groq_llm is None:
            self.logger.warning("Groq LLM not available for classification")
            return []
        
        try:
            domains_list = ", ".join(LEGAL_DOMAINS)
            
            system_prompt = """You are an expert legal domain classification specialist for Indian law. Your task is to accurately classify legal queries into the most appropriate legal domains.

AVAILABLE DOMAINS: """ + domains_list + """

CLASSIFICATION GUIDELINES:
1. Analyze the query comprehensively to identify all relevant legal domains
2. Consider primary legal areas, secondary related areas, and cross-cutting issues
3. Return 1-3 most relevant domains in order of relevance
4. Be precise - only classify into domains that are clearly relevant
5. Consider Indian legal framework and jurisdiction

OUTPUT FORMAT:
Return ONLY a JSON array of domain names (1-3 domains) in order of relevance.
Example: ["consumer_protection", "civic_rights"]

IMPORTANT: Only use domains from the available list. Be accurate and precise."""

            user_prompt = f"""Classify this legal query into the most appropriate legal domain(s):

Query: {query}

Return a JSON array of domain names (1-3 domains). Only use domains from the available list."""

            result = groq_llm.generate_response(
                prompt=f"{system_prompt}\n\n{user_prompt}",
                temperature=0.2,
                max_tokens=200
            )
            
            if not result:
                return []
            
            # Try to extract JSON array from response
            result = result.strip()
            
            # Remove markdown code blocks if present
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
                result = result.strip()
            
            # Parse JSON
            try:
                domains = json.loads(result)
                if isinstance(domains, list):
                    # Validate domains are in the allowed list
                    valid_domains = [d for d in domains if d in LEGAL_DOMAINS]
                    if valid_domains:
                        self.logger.info(f"✓ LLM classified into: {valid_domains}")
                        return valid_domains[:3]
            except json.JSONDecodeError:
                # Try to extract domains from text response
                domains = []
                for domain in LEGAL_DOMAINS:
                    if domain.lower() in result.lower():
                        domains.append(domain)
                if domains:
                    self.logger.info(f"✓ LLM classified (extracted): {domains}")
                    return domains[:3]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error in LLM classification: {e}", exc_info=True)
            return []