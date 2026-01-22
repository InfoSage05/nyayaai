"""Tavily Search API integration for real-time web search."""
import logging
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

TAVILY_AVAILABLE = False
TavilyClient = None

try:
    from tavily import TavilyClient as _TavilyClient
    TavilyClient = _TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    logger.warning("tavily-python package not installed. Web search will not be available.")
    TAVILY_AVAILABLE = False


class TavilySearch:
    """Tavily search utility for real-time legal information retrieval."""
    
    def __init__(self):
        """Initialize Tavily client."""
        if not TAVILY_AVAILABLE:
            raise ImportError(
                "tavily-python package is not installed. "
                "Install it with: pip install tavily-python"
            )
        
        self.api_key = getattr(settings, 'tavily_api_key', None)
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not set. Web search will not work.")
            self.client = None
        else:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Tavily client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
                self.client = None
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False
    ) -> List[Dict[str, Any]]:
        """Search the web using Tavily API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)
            search_depth: Search depth - "basic" or "advanced" (default: "advanced")
            include_domains: List of domains to include in search
            exclude_domains: List of domains to exclude from search
            include_answer: Whether to include AI-generated answer (default: True)
            include_raw_content: Whether to include raw content (default: False)
            
        Returns:
            List of search results with title, url, content, score, etc.
        """
        if not self.client:
            logger.warning("Tavily client not available")
            return []
        
        try:
            # Build search parameters
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "include_raw_content": include_raw_content
            }
            
            if include_domains:
                search_params["include_domains"] = include_domains
            
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
            
            # Perform search
            response = self.client.search(**search_params)
            
            # Format results
            results = []
            if response and hasattr(response, 'results'):
                for result in response.results:
                    results.append({
                        "title": getattr(result, 'title', ''),
                        "url": getattr(result, 'url', ''),
                        "content": getattr(result, 'content', ''),
                        "score": getattr(result, 'score', 0.0),
                        "published_date": getattr(result, 'published_date', None),
                        "raw_content": getattr(result, 'raw_content', '') if include_raw_content else None
                    })
            
            # Include AI-generated answer if available
            if include_answer and hasattr(response, 'answer'):
                results.insert(0, {
                    "title": "AI-Generated Answer",
                    "url": None,
                    "content": response.answer,
                    "score": 1.0,
                    "published_date": None,
                    "raw_content": None,
                    "is_answer": True
                })
            
            logger.info(f"Tavily search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error performing Tavily search: {e}", exc_info=True)
            return []
    
    def search_legal_info(
        self,
        query: str,
        max_results: int = 5,
        include_recent_updates: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for legal information with optimized parameters.
        
        Args:
            query: Legal query string
            max_results: Maximum number of results
            include_recent_updates: Whether to prioritize recent legal updates
            
        Returns:
            List of legal information search results
        """
        # Include legal domains
        include_domains = [
            "indiankanoon.org",
            "legislative.gov.in",
            "lawcommissionofindia.nic.in",
            "judis.nic.in",
            "main.sci.gov.in"
        ]
        
        return self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_domains=include_domains,
            include_answer=True,
            include_raw_content=False
        )


# Global Tavily search instance
_tavily_instance = None

def get_tavily_search() -> Optional[TavilySearch]:
    """Get or create global Tavily search instance."""
    global _tavily_instance
    if _tavily_instance is None and TAVILY_AVAILABLE:
        try:
            _tavily_instance = TavilySearch()
        except Exception as e:
            logger.warning(f"Could not initialize Tavily search: {e}")
            return None
    return _tavily_instance
