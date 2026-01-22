"""Script to set up all Qdrant collections for NyayaAI."""
import logging
from .qdrant_client import qdrant_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Collection definitions - Comprehensive list
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
    },
    "case_similarity_vectors": {
        "vector_size": 384,
        "description": "Case similarity data for matching"
    }
}


def setup_all_collections():
    """Create all required Qdrant collections.
    
    This function checks if collections exist before creating them,
    and provides detailed logging for each collection.
    
    Returns:
        dict: Status of each collection setup
    """
    logger.info("="*80)
    logger.info("SETTING UP QDRANT COLLECTIONS FOR NYAYAAI")
    logger.info("="*80)
    
    results = {}
    
    for collection_name, config in COLLECTIONS.items():
        logger.info(f"\nSetting up collection: {collection_name}")
        logger.info(f"  Description: {config['description']}")
        logger.info(f"  Vector size: {config['vector_size']}")
        
        # Check if collection already exists
        existing_info = qdrant_manager.get_collection_info(collection_name)
        if existing_info:
            points_count = existing_info.get("points_count", 0)
            logger.info(f"  ✓ Collection '{collection_name}' already exists ({points_count:,} vectors)")
            results[collection_name] = {"status": "exists", "points": points_count}
        else:
            # Create new collection
            success = qdrant_manager.create_collection(
                collection_name=collection_name,
                vector_size=config["vector_size"]
            )
            if success:
                logger.info(f"  ✓ Collection '{collection_name}' created successfully")
                results[collection_name] = {"status": "created", "points": 0}
            else:
                logger.error(f"  ✗ Failed to create collection '{collection_name}'")
                results[collection_name] = {"status": "failed", "points": 0}
    
    logger.info("\n" + "="*80)
    logger.info("COLLECTION SETUP SUMMARY")
    logger.info("="*80)
    
    created = sum(1 for r in results.values() if r["status"] == "created")
    existing = sum(1 for r in results.values() if r["status"] == "exists")
    failed = sum(1 for r in results.values() if r["status"] == "failed")
    total_points = sum(r["points"] for r in results.values())
    
    logger.info(f"  Created: {created}")
    logger.info(f"  Existing: {existing}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total vectors: {total_points:,}")
    logger.info("="*80 + "\n")
    
    return results


if __name__ == "__main__":
    setup_all_collections()
