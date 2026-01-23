"""Qdrant client wrapper and utilities."""
from typing import List, Dict, Any, Optional
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

# Optional imports - handle gracefully if qdrant_client is not installed
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    logger.warning("qdrant_client not installed. Qdrant operations will not work.")
    QdrantClient = None
    Distance = None
    VectorParams = None
    PointStruct = None
    QDRANT_AVAILABLE = False


class QdrantManager:
    """Manages Qdrant connections and operations."""
    
    def __init__(self):
        """Initialize Qdrant client (lazy connection)."""
        self._client = None
        self._connected = False
    
    @property
    def client(self) -> QdrantClient:
        """Get Qdrant client with lazy connection."""
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant_client package is not installed. Install it with: pip install qdrant-client")
        
        if self._client is None:
            try:
                # For local Qdrant, don't use HTTPS or API key
                # For cloud Qdrant, use URL and API key
                if settings.qdrant_api_key:
                    # Cloud Qdrant
                    self._client = QdrantClient(
                        url=f"https://{settings.qdrant_host}",
                        api_key=settings.qdrant_api_key,
                    )
                    logger.info(f"Connected to cloud Qdrant")
                else:
                    # Local Qdrant (default)
                    # Don't use timeout in constructor - it might cause issues
                    # Connection will be tested on first operation
                    self._client = QdrantClient(
                        host=settings.qdrant_host,
                        port=settings.qdrant_port,
                    )
                    # Test connection with a simple operation
                    try:
                        self._client.get_collections()
                        logger.info(f"Connected to local Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
                    except Exception as conn_err:
                        logger.warning(f"Qdrant connection test failed: {conn_err}")
                        logger.info("Qdrant may not be running. Start with: docker compose up -d qdrant")
                        # Keep client but mark as potentially unavailable
                        self._connected = False
                        raise ConnectionError(f"Qdrant not available at {settings.qdrant_host}:{settings.qdrant_port}. Start Docker: docker compose up -d qdrant")
                self._connected = True
            except (ConnectionError, ImportError):
                # Re-raise connection/import errors
                raise
            except Exception as e:
                logger.warning(f"Could not connect to Qdrant: {e}. Operations will fail gracefully.")
                self._connected = False
                raise ConnectionError(f"Qdrant not available: {e}")
        return self._client
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 384,  # all-MiniLM-L6-v2 dimension
        distance = None
    ) -> bool:
        """Create a Qdrant collection if it doesn't exist."""
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant_client package is not installed")
        
        if distance is None:
            distance = Distance.COSINE if Distance else None
        
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
        points: List[Any]
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
# Initialize immediately - connection is lazy (only when client property is accessed)
qdrant_manager = QdrantManager()
