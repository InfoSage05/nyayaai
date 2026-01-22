"""
PHASE 1: Complete Data Ingestion for NyayaAI

This script:
1. Creates collections in Qdrant
2. Ingests sample legal data
3. Verifies vectors are stored
4. Reports statistics

Run once to populate the vector database.
"""

import logging
import sys
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embeddings
from qdrant_client.models import PointStruct
import uuid
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PHASE 1 STEP 1: Initialize Collections
# ============================================================================

def initialize_collections():
    """Create all required Qdrant collections."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 STEP 1: Initializing Collections")
    logger.info("="*80)
    
    collections = {
        "statutes_vectors": "Indian statutes and laws",
        "case_law_vectors": "Court judgments and case laws",
        "civic_process_vectors": "Civic processes and procedures"
    }
    
    for collection_name, description in collections.items():
        success = qdrant_manager.create_collection(
            collection_name=collection_name,
            vector_size=384,  # all-MiniLM-L6-v2 dimension
        )
        if success:
            logger.info(f"✓ Collection '{collection_name}' ready: {description}")
        else:
            logger.error(f"✗ Failed to create collection '{collection_name}'")
            return False
    
    logger.info("✓ All collections initialized successfully\n")
    return True


# ============================================================================
# PHASE 1 STEP 2: Ingest Sample Legal Data
# ============================================================================

def ingest_sample_data():
    """Ingest comprehensive sample legal data into Qdrant."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 STEP 2: Ingesting Sample Legal Data")
    logger.info("="*80)
    
    # Sample statutes data
    statutes_data = [
        {
            "title": "Right to Information Act, 2005",
            "content": "The Right to Information Act, 2005 (RTI) provides citizens the right to seek information from public authorities. Any person can request information about government activities and decisions.",
            "source": "indiacode",
            "url": "https://www.indiacode.nic.in/rti",
            "doc_type": "statute"
        },
        {
            "title": "RTI Application Procedure",
            "content": "To file an RTI application: 1. Identify the public authority 2. Prepare written application with specific details 3. Submit with fees (₹10) 4. Track application online. Response must be provided within 30 days.",
            "source": "civic_process",
            "url": "https://rtionline.gov.in",
            "doc_type": "procedure"
        },
        {
            "title": "Right to Information Rules, 2012",
            "content": "These rules provide detailed procedures for implementing the RTI Act. Central Public Information Officer (CPIO) must be appointed. Fees for photocopying are prescribed at ₹2 per page.",
            "source": "indiacode",
            "url": "https://www.indiacode.nic.in/rules",
            "doc_type": "rules"
        },
        {
            "title": "Indian Constitution Article 21",
            "content": "Article 21 - Protection of life and personal liberty. No person shall be deprived of his life or personal liberty except according to procedure established by law.",
            "source": "indiacode",
            "url": "https://www.indiacode.nic.in/constitution",
            "doc_type": "constitutional"
        },
        {
            "title": "National Archives Act, 2016",
            "content": "This Act governs the management and preservation of national archives. Public records are generally open for access after 30 years.",
            "source": "indiacode",
            "url": "https://www.indiacode.nic.in/archives",
            "doc_type": "statute"
        }
    ]
    
    # Sample case law data
    case_law_data = [
        {
            "title": "S.P. Gupta v. Union of India (1981)",
            "content": "This landmark judgment established the right to information as a fundamental right under Article 21. The court held that citizens have a basic right to know about government functioning.",
            "source": "supremecourt",
            "url": "https://main.sci.gov.in/judgments",
            "doc_type": "judgment"
        },
        {
            "title": "Hamdard Dawakhana v. Union of India (1992)",
            "content": "The Supreme Court held that the RTI applies to all types of public authorities including autonomous bodies and institutions receiving public funds.",
            "source": "supremecourt",
            "url": "https://main.sci.gov.in/judgments",
            "doc_type": "judgment"
        },
        {
            "title": "Reliance Petrochemicals Ltd. v. I.R.C. (2007)",
            "content": "Court ruled that trade secrets and commercial confidentiality are exemptions under RTI but cannot be used to withhold all information.",
            "source": "supremecourt",
            "url": "https://main.sci.gov.in/judgments",
            "doc_type": "judgment"
        },
        {
            "title": "Subhash Chandra Agarwal v. CIC (2009)",
            "content": "This judgment clarified that third-party information held by government must be disclosed unless it falls under specific exemptions.",
            "source": "supremecourt",
            "url": "https://main.sci.gov.in/judgments",
            "doc_type": "judgment"
        },
        {
            "title": "Bennett Coleman v. CIC (2013)",
            "content": "Court upheld that RTI provisions apply to media and information organizations that receive government funding.",
            "source": "supremecourt",
            "url": "https://main.sci.gov.in/judgments",
            "doc_type": "judgment"
        }
    ]
    
    # Ingest statutes
    logger.info("\nIngesting statutes and laws...")
    statute_count = ingest_documents(statutes_data, "statutes_vectors")
    
    # Ingest case law
    logger.info("\nIngesting case law and judgments...")
    case_count = ingest_documents(case_law_data, "case_law_vectors")
    
    logger.info("\n" + "-"*80)
    logger.info(f"✓ Ingested {statute_count} statutes into 'statutes_vectors'")
    logger.info(f"✓ Ingested {case_count} case laws into 'case_law_vectors'")
    logger.info("-"*80 + "\n")
    
    return statute_count > 0 and case_count > 0


def ingest_documents(documents, collection_name):
    """Embed and ingest documents into Qdrant."""
    points = []
    
    for doc in documents:
        # Get embedding (returns list of embeddings, extract the first one)
        embeddings = get_embeddings(doc["content"])
        embedding = embeddings[0]  # Extract single embedding as List[float]
        
        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "title": doc["title"],
                "content": doc["content"],
                "source": doc["source"],
                "url": doc["url"],
                "doc_type": doc["doc_type"],
                "ingested_at": datetime.now().isoformat(),
                "collection": collection_name
            }
        )
        points.append(point)
        logger.info(f"  • Embedded: {doc['title']}")
    
    # Upsert all points
    success = qdrant_manager.upsert_points(collection_name, points)
    
    if success:
        logger.info(f"  ✓ Successfully upserted {len(points)} documents")
    else:
        logger.error(f"  ✗ Failed to upsert documents")
    
    return len(points) if success else 0


# ============================================================================
# PHASE 1 STEP 3: Verify Data in Qdrant
# ============================================================================

def verify_ingestion():
    """Verify that data was properly ingested into Qdrant."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 STEP 3: Verifying Ingestion")
    logger.info("="*80)
    
    collections = ["statutes_vectors", "case_law_vectors", "civic_process_vectors"]
    total_vectors = 0
    all_verified = True
    
    for collection_name in collections:
        info = qdrant_manager.get_collection_info(collection_name)
        
        if info:
            count = info.get("points_count", 0)
            total_vectors += count
            
            if count > 0:
                logger.info(f"✓ {collection_name}: {count} vectors")
            else:
                logger.warning(f"⚠ {collection_name}: {count} vectors (empty)")
                all_verified = False
        else:
            logger.error(f"✗ {collection_name}: Collection not found")
            all_verified = False
    
    logger.info("-"*80)
    logger.info(f"Total vectors in database: {total_vectors}")
    logger.info("-"*80 + "\n")
    
    if total_vectors >= 5:
        logger.info("✓ Minimum vector requirement met (>= 5)")
        return True
    else:
        logger.error("✗ Insufficient vectors in database")
        return False


# ============================================================================
# PHASE 1 STEP 4: Test Retrieval
# ============================================================================

def test_retrieval():
    """Test that retrieval works with sample queries."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 1 STEP 4: Testing Retrieval")
    logger.info("="*80)
    
    test_queries = [
        "How do I file an RTI application?",
        "What is the right to information?",
        "RTI application fees and procedure"
    ]
    
    all_working = True
    
    for query in test_queries:
        logger.info(f"\nQuery: '{query}'")
        
        query_embeddings = get_embeddings(query)
        query_embedding = query_embeddings[0]  # Extract first embedding
        
        # Try retrieving from statutes
        results = qdrant_manager.search(
            collection_name="statutes_vectors",
            query_vector=query_embedding,
            limit=2,
            score_threshold=0.3
        )
        
        if results:
            logger.info(f"  ✓ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                score = result.get("score", 0)
                title = result.get("payload", {}).get("title", "Unknown")
                logger.info(f"    {i}. {title} (score: {score:.4f})")
        else:
            logger.warning(f"  ⚠ No results found")
            all_working = False
    
    logger.info("\n" + "-"*80 + "\n")
    return all_working


# ============================================================================
# PHASE 1 MAIN: Run Complete Ingestion
# ============================================================================

def main():
    """Run complete Phase 1 ingestion."""
    logger.info("\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "NYAYAAI PHASE 1: DATA INGESTION" + " "*27 + "║")
    logger.info("║" + " "*20 + "Vector Database Population" + " "*32 + "║")
    logger.info("╚" + "="*78 + "╝")
    
    try:
        # Step 1: Initialize Collections
        if not initialize_collections():
            logger.error("Failed to initialize collections")
            return False
        
        # Step 2: Ingest Sample Data
        if not ingest_sample_data():
            logger.error("Failed to ingest sample data")
            return False
        
        # Step 3: Verify Ingestion
        if not verify_ingestion():
            logger.error("Ingestion verification failed")
            return False
        
        # Step 4: Test Retrieval
        if not test_retrieval():
            logger.warning("Some retrieval tests failed")
        
        # Success
        logger.info("\n" + "╔" + "="*78 + "╗")
        logger.info("║" + " "*25 + "✓ PHASE 1 COMPLETE" + " "*35 + "║")
        logger.info("║" + " "*15 + "Data has been successfully ingested into Qdrant" + " "*17 + "║")
        logger.info("║" + " "*20 + "Ready for retrieval and agent pipeline" + " "*21 + "║")
        logger.info("╚" + "="*78 + "╝\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Ingestion failed with error: {e}")
        logger.exception(e)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
