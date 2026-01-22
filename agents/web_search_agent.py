"""Web Search Agent - Searches public web for reliable legal information."""
from typing import Dict, Any, List
from core.agent_base import BaseAgent, AgentInput, AgentOutput
from utils.tavily_search import get_tavily_search


class WebSearchAgent(BaseAgent):
    """Searches the public web for reliable legal information."""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Searches public web for reliable government or educational legal information"
        )
    
    def process(self, input_data: AgentInput) -> AgentOutput:
        """Search the web for reliable legal information.
        
        Args:
            input_data: Query for web search
            
        Returns:
            Web search results from reliable sources
        """
        if not self.validate_input(input_data):
            return AgentOutput(
                result=None,
                confidence=0.0,
                reasoning="Invalid input",
                agent_name=self.name
            )
        
        tavily = get_tavily_search()
        if not tavily or not tavily.client:
            return AgentOutput(
                result={"web_results": [], "count": 0},
                confidence=0.0,
                reasoning="Web search not available",
                agent_name=self.name
            )
        
        try:
            # Search for reliable legal information
            search_query = f"{input_data.query} Indian law official sources"
            web_results = tavily.search(
                query=search_query,
                max_results=5,
                include_domains=[
                    "gov.in", "indiankanoon.org", "supremecourtofindia.nic.in",
                    "legislative.gov.in", "lawcommissionofindia.nic.in",
                    "worldlii.org", "edu"
                ]
            )
            
            # Format results
            formatted_results = []
            for result in web_results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0)
                })
            
            confidence = len(formatted_results) * 0.2  # Basic confidence based on results count
            
            return AgentOutput(
                result={
                    "web_results": formatted_results,
                    "count": len(formatted_results)
                },
                confidence=min(confidence, 1.0),
                reasoning=f"Retrieved {len(formatted_results)} web search results from reliable sources",
                agent_name=self.name,
                metadata={
                    "search_query": search_query,
                    "sources_focused": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return AgentOutput(
                result={"web_results": [], "count": 0},
                confidence=0.0,
                reasoning=f"Web search error: {str(e)}",
                agent_name=self.name
            )