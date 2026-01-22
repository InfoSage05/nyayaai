"""Script to set up all Qdrant collections for NyayaAI."""
import logging
from .qdrant_client import qdrant_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Collection definitions
COLLECTIONS = {
    "legal_taxonomy_vectors": {
        "vector_size": 384,
        "description": "Legal domain taxonomy and classification"
    },
    "statutes_vectors": {
        "vector_size": 384,
        "description": "Legal statutes, acts, and regulations"
    },
    "case_law_vectors": {
        "vector_size": 384,
        "description": "Case law and judicial judgments"
    },
    "civic_process_vectors": {
        "vector_size": 384,
        "description": "Civic processes and procedures"
    },
    "case_memory_vectors": {
        "vector_size": 384,
        "description": "Long-term case memory"
    },
    "user_interaction_memory": {
        "vector_size": 384,
        "description": "User interaction history"
    }
}


def setup_all_collections():
    """Create all required Qdrant collections."""
    logger.info("Setting up Qdrant collections for NyayaAI...")
    
    for collection_name, config in COLLECTIONS.items():
        logger.info(f"Setting up collection: {collection_name}")
        success = qdrant_manager.create_collection(
            collection_name=collection_name,
            vector_size=config["vector_size"]
        )
        if success:
            logger.info(f"✓ Collection '{collection_name}' ready")
        else:
            logger.error(f"✗ Failed to create collection '{collection_name}'")
    
    logger.info("Collection setup complete!")


if __name__ == "__main__":
    setup_all_collections()
