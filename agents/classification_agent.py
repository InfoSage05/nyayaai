"""Legal Domain Classification Agent - Classifies queries into legal domains."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embedding

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
        
        # Get embedding from context or generate new
        context = input_data.context or {}
        if "embedding" in context:
            query_embedding = context["embedding"]
        else:
            query_embedding = get_embedding(input_data.query)
        
        # Search legal taxonomy collection
        results = qdrant_manager.search(
            collection_name="legal_taxonomy_vectors",
            query_vector=query_embedding,
            limit=3,
            score_threshold=0.4
        )
        
        self.log_retrieval("legal_taxonomy_vectors", len(results), 0.4)
        
        # Extract domains from retrieved taxonomy
        classified_domains = []
        if results:
            for result in results:
                domain = result["payload"].get("domain", "")
                if domain and domain not in classified_domains:
                    classified_domains.append(domain)
        
        # Fallback: use keyword matching if no taxonomy match
        if not classified_domains:
            classified_domains = self._keyword_classify(input_data.query)
        
        confidence = results[0]["score"] if results else 0.5
        
        return AgentOutput(
            result={
                "domains": classified_domains,
                "primary_domain": classified_domains[0] if classified_domains else "general"
            },
            retrieved_documents=results,
            confidence=float(confidence),
            reasoning=f"Classified into {len(classified_domains)} domain(s) using taxonomy search",
            agent_name=self.name,
            metadata={
                "taxonomy_results_count": len(results),
                "fallback_used": len(results) == 0
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
