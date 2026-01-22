#!/usr/bin/env python
"""
UNIFIED DATA INGESTION SCRIPT FOR NYAYAAI

This script does everything in one run:
1. Sets up all Qdrant collections
2. Ingests data from all available connectors:
   - Data.gov.in (government datasets)
   - IndiaCode (acts and statutes)
   - Supreme Court of India (judgments)
   - WorldLII/IndianLII (case law)
   - Law Commission of India (reports)
3. Ingests sample data as fallback
4. Verifies ingestion and reports statistics

Run once to populate the entire vector database.
"""

import logging
import sys
import time
import uuid
from typing import List, Dict, Tuple
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import connectors
from database.qdrant_client import qdrant_manager
from database.setup_collections import setup_all_collections
from database.ingest_sample_data import ingest_all as ingest_sample_data
from connectors.data_gov_connector import ingest_from_datagov_dataset
from connectors.indiacode_connector import ingest_act_from_url
from connectors.supremecourt_connector import ingest_judgment
from connectors.worldlii_connector import ingest_case
from connectors.lawcommission_connector import ingest_report
from utils.embeddings import get_embeddings
from qdrant_client.models import PointStruct


# =============================================================================
# DATA SOURCES CONFIGURATION
# =============================================================================

DATA_GOV_DATASETS = [
    "https://data.gov.in/api/3/action/package_show?id=justice-sector-statistics",
    "https://data.gov.in/api/3/action/package_show?id=courts-portal",
    "https://data.gov.in/api/3/action/package_show?id=constitutional-framework",
]

INDIACODE_ACTS = [
    "https://www.indiacode.nic.in/handle/123456789/1362",  # RTI Act
    "https://www.indiacode.nic.in/handle/123456789/2263",  # Consumer Protection Act
    "https://www.indiacode.nic.in/handle/123456789/1363",  # Constitution of India
]

SUPREME_COURT_CASES = [
    "https://main.sci.gov.in/judgments",
    # Add specific judgment URLs here
]

WORLDLII_CASES = [
    "https://www.indlii.org/in/cases/INSC/2019/39.html",
    "https://www.indlii.org/in/cases/INSC/2017/87.html",
    "https://www.worldlii.org/int/cases/INSC/1997/3011.html",
]

LAW_COMMISSION_REPORTS = [
    "https://lawcommissionofindia.nic.in/reports/rep200.pdf",
    "https://lawcommissionofindia.nic.in/reports/rep277.pdf",
]


# =============================================================================
# STAGE 1: SETUP COLLECTIONS
# =============================================================================

def stage_1_setup_collections() -> bool:
    """Set up all Qdrant collections."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 1: SETTING UP COLLECTIONS")
    logger.info("="*80)
    
    try:
        setup_all_collections()
        logger.info("✓ All collections ready")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to setup collections: {e}")
        return False


# =============================================================================
# STAGE 2: DATA.GOV.IN INGESTION
# =============================================================================

def stage_2_datagov() -> Tuple[int, List[str]]:
    """Ingest from Data.gov.in."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 2: INGESTING FROM DATA.GOV.IN")
    logger.info("="*80)
    
    total_ingested = 0
    errors = []
    
    for idx, dataset_url in enumerate(DATA_GOV_DATASETS, 1):
        logger.info(f"\nDataset {idx}/{len(DATA_GOV_DATASETS)}: {dataset_url}")
        try:
            success = ingest_from_datagov_dataset(dataset_url, "statutes_vectors")
            if success:
                total_ingested += 1
                logger.info(f"  ✓ Ingested dataset")
            else:
                errors.append(f"Failed: {dataset_url}")
                logger.warning(f"  ⚠ Failed to ingest dataset")
        except Exception as e:
            error_msg = f"Error ingesting {dataset_url}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"  ✗ {error_msg}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 2 COMPLETE: Processed {len(DATA_GOV_DATASETS)} datasets")
    return total_ingested, errors


# =============================================================================
# STAGE 3: INDIACODE INGESTION
# =============================================================================

def stage_3_indiacode() -> Tuple[int, List[str]]:
    """Ingest from IndiaCode."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 3: INGESTING FROM INDIACODE")
    logger.info("="*80)
    
    total_ingested = 0
    errors = []
    
    for idx, act_url in enumerate(INDIACODE_ACTS, 1):
        logger.info(f"\nAct {idx}/{len(INDIACODE_ACTS)}: {act_url}")
        try:
            success = ingest_act_from_url(act_url, "statutes_vectors")
            if success:
                total_ingested += 1
                logger.info(f"  ✓ Ingested act")
            else:
                errors.append(f"Failed: {act_url}")
                logger.warning(f"  ⚠ Failed to ingest act")
        except Exception as e:
            error_msg = f"Error ingesting {act_url}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"  ✗ {error_msg}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 3 COMPLETE: Processed {len(INDIACODE_ACTS)} acts")
    return total_ingested, errors


# =============================================================================
# STAGE 4: SUPREME COURT INGESTION
# =============================================================================

def stage_4_supremecourt() -> Tuple[int, List[str]]:
    """Ingest from Supreme Court of India."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 4: INGESTING FROM SUPREME COURT OF INDIA")
    logger.info("="*80)
    
    total_ingested = 0
    errors = []
    
    # Note: Supreme Court URLs may need to be specific judgment URLs
    # For now, we'll try to ingest from the main judgments page
    for idx, case_url in enumerate(SUPREME_COURT_CASES, 1):
        logger.info(f"\nCase {idx}/{len(SUPREME_COURT_CASES)}: {case_url}")
        try:
            success = ingest_judgment(case_url, "case_law_vectors")
            if success:
                total_ingested += 1
                logger.info(f"  ✓ Ingested judgment")
            else:
                errors.append(f"Failed: {case_url}")
                logger.warning(f"  ⚠ Failed to ingest judgment")
        except Exception as e:
            error_msg = f"Error ingesting {case_url}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"  ✗ {error_msg}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 4 COMPLETE: Processed {len(SUPREME_COURT_CASES)} cases")
    return total_ingested, errors


# =============================================================================
# STAGE 5: WORLDLII INGESTION
# =============================================================================

def stage_5_worldlii() -> Tuple[int, List[str]]:
    """Ingest from WorldLII/IndianLII."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 5: INGESTING FROM WORLDLII/INDIANLII")
    logger.info("="*80)
    
    total_ingested = 0
    errors = []
    
    for idx, case_url in enumerate(WORLDLII_CASES, 1):
        logger.info(f"\nCase {idx}/{len(WORLDLII_CASES)}: {case_url}")
        try:
            success = ingest_case(case_url, "case_law_vectors")
            if success:
                total_ingested += 1
                logger.info(f"  ✓ Ingested case")
            else:
                errors.append(f"Failed: {case_url}")
                logger.warning(f"  ⚠ Failed to ingest case")
        except Exception as e:
            error_msg = f"Error ingesting {case_url}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"  ✗ {error_msg}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 5 COMPLETE: Processed {len(WORLDLII_CASES)} cases")
    return total_ingested, errors


# =============================================================================
# STAGE 6: LAW COMMISSION INGESTION
# =============================================================================

def stage_6_lawcommission() -> Tuple[int, List[str]]:
    """Ingest from Law Commission of India."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 6: INGESTING FROM LAW COMMISSION OF INDIA")
    logger.info("="*80)
    
    total_ingested = 0
    errors = []
    
    for idx, report_url in enumerate(LAW_COMMISSION_REPORTS, 1):
        logger.info(f"\nReport {idx}/{len(LAW_COMMISSION_REPORTS)}: {report_url}")
        try:
            success = ingest_report(report_url, "legal_taxonomy_vectors")
            if success:
                total_ingested += 1
                logger.info(f"  ✓ Ingested report")
            else:
                errors.append(f"Failed: {report_url}")
                logger.warning(f"  ⚠ Failed to ingest report")
        except Exception as e:
            error_msg = f"Error ingesting {report_url}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"  ✗ {error_msg}")
        
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 6 COMPLETE: Processed {len(LAW_COMMISSION_REPORTS)} reports")
    return total_ingested, errors


# =============================================================================
# STAGE 7: SAMPLE DATA INGESTION (FALLBACK)
# =============================================================================

def stage_7_sample_data() -> Tuple[int, List[str]]:
    """Ingest sample data as fallback."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 7: INGESTING SAMPLE DATA (FALLBACK)")
    logger.info("="*80)
    
    try:
        results = ingest_sample_data()
        total_ingested = sum(1 for v in results.values() if v)
        logger.info(f"\n✓ STAGE 7 COMPLETE: Ingested sample data")
        return total_ingested, []
    except Exception as e:
        error_msg = f"Error ingesting sample data: {str(e)}"
        logger.error(f"  ✗ {error_msg}")
        return 0, [error_msg]


# =============================================================================
# STAGE 8: VERIFICATION
# =============================================================================

def stage_8_verification() -> Dict:
    """Verify ingestion and generate statistics."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 8: VERIFICATION & STATISTICS")
    logger.info("="*80)
    
    collections = [
        "legal_taxonomy_vectors",
        "statutes_vectors",
        "case_law_vectors",
        "civic_process_vectors",
        "case_memory_vectors",
        "user_interaction_memory",
    ]
    
    stats = {
        "total_vectors": 0,
        "collection_stats": {},
        "verification_timestamp": datetime.now().isoformat(),
    }
    
    for collection in collections:
        try:
            info = qdrant_manager.get_collection_info(collection)
            if info:
                points_count = info.get("points_count", 0)
                stats["collection_stats"][collection] = points_count
                stats["total_vectors"] += points_count
                logger.info(f"  ✓ {collection}: {points_count:,} vectors")
            else:
                stats["collection_stats"][collection] = 0
                logger.warning(f"  ⚠ {collection}: No data")
        except Exception as e:
            logger.warning(f"  ⚠ {collection}: {e}")
            stats["collection_stats"][collection] = 0
    
    logger.info(f"\n✓ STAGE 8 COMPLETE: {stats['total_vectors']:,} total vectors verified")
    return stats


# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def main():
    """Execute complete unified ingestion pipeline."""
    logger.info("\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "NYAYAAI UNIFIED DATA INGESTION" + " "*27 + "║")
    logger.info("║" + " "*25 + "Complete Vector Database Setup" + " "*25 + "║")
    logger.info("╚" + "="*78 + "╝")
    
    start_time = time.time()
    results = {}
    
    try:
        # Stage 1: Setup collections
        if not stage_1_setup_collections():
            logger.error("Failed to setup collections. Aborting.")
            return 1
        results["setup"] = True
        
        # Stage 2: Data.gov.in
        datagov_count, datagov_errors = stage_2_datagov()
        results["datagov"] = {"ingested": datagov_count, "errors": datagov_errors}
        
        # Stage 3: IndiaCode
        indiacode_count, indiacode_errors = stage_3_indiacode()
        results["indiacode"] = {"ingested": indiacode_count, "errors": indiacode_errors}
        
        # Stage 4: Supreme Court
        sc_count, sc_errors = stage_4_supremecourt()
        results["supremecourt"] = {"ingested": sc_count, "errors": sc_errors}
        
        # Stage 5: WorldLII
        worldlii_count, worldlii_errors = stage_5_worldlii()
        results["worldlii"] = {"ingested": worldlii_count, "errors": worldlii_errors}
        
        # Stage 6: Law Commission
        lc_count, lc_errors = stage_6_lawcommission()
        results["lawcommission"] = {"ingested": lc_count, "errors": lc_errors}
        
        # Stage 7: Sample Data
        sample_count, sample_errors = stage_7_sample_data()
        results["sample_data"] = {"ingested": sample_count, "errors": sample_errors}
        
        # Stage 8: Verification
        verification_stats = stage_8_verification()
        results["verification"] = verification_stats
        
        # Final Summary
        logger.info("\n" + "="*80)
        logger.info("FINAL INGESTION SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\n📋 SOURCES PROCESSED:")
        logger.info(f"  • Data.gov.in:        {datagov_count} datasets")
        logger.info(f"  • IndiaCode:          {indiacode_count} acts")
        logger.info(f"  • Supreme Court:      {sc_count} cases")
        logger.info(f"  • WorldLII/IndianLII: {worldlii_count} cases")
        logger.info(f"  • Law Commission:      {lc_count} reports")
        logger.info(f"  • Sample Data:         {sample_count} collections")
        
        logger.info(f"\n📦 COLLECTIONS STATUS:")
        for collection, count in verification_stats["collection_stats"].items():
            status = "✓" if count > 0 else "○"
            logger.info(f"  {status} {collection}: {count:,} vectors")
        
        elapsed = time.time() - start_time
        logger.info(f"\n⏱️  PERFORMANCE:")
        logger.info(f"  • Total Time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        if verification_stats["total_vectors"] > 0:
            logger.info(f"  • Vectors/sec: {verification_stats['total_vectors']/elapsed:.1f}")
        
        logger.info(f"\n✅ UNIFIED INGESTION COMPLETE!")
        logger.info("="*80)
        
        return 0
    
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}", exc_info=True)
        logger.info("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
