"""Qdrant client wrapper and utilities."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
import logging

from config.settings import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    """Manages Qdrant connections and operations."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        # For local Qdrant, don't use HTTPS or API key
        # For cloud Qdrant, use URL and API key
        if settings.qdrant_api_key:
            # Cloud Qdrant
            self.client = QdrantClient(
                url=f"https://{settings.qdrant_host}",
                api_key=settings.qdrant_api_key,
            )
            logger.info(f"Connected to cloud Qdrant")
        else:
            # Local Qdrant (default)
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            logger.info(f"Connected to local Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 384,  # all-MiniLM-L6-v2 dimension
        distance: Distance = Distance.COSINE
    ) -> bool:
        """Create a Qdrant collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name in collection_names:
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                ),
            )
            logger.info(f"Created collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False
    
    def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> bool:
        """Insert or update points in a collection."""
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} points to {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error upserting points to {collection_name}: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a collection."""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            query_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results.points
            ]
        except Exception as e:
            logger.error(f"Error searching {collection_name}: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection."""
        try:
            info = self.client.get_collection(collection_name)
            # vectors is a dict or VectorParams, default to 384
            vector_size = 384
            if hasattr(info.config.params, 'vectors') and info.config.params.vectors:
                if isinstance(info.config.params.vectors, dict):
                    first_vector = next(iter(info.config.params.vectors.values()), None)
                    if first_vector and hasattr(first_vector, 'size'):
                        vector_size = first_vector.size
                elif hasattr(info.config.params.vectors, 'size'):
                    vector_size = info.config.params.vectors.size
            return {
                "name": collection_name,
                "vector_size": vector_size,
                "vectors_count": info.points_count,
                "points_count": info.points_count,
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return None


# Global Qdrant manager instance
qdrant_manager = QdrantManager()
