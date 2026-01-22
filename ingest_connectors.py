#!/usr/bin/env python
"""
COMPREHENSIVE CONNECTOR DATA INGESTION - FINAL VERSION

Systematic ingestion of legal data from all sources into Qdrant vector database.
This is the FINAL, PRODUCTION-READY ingestion script with:
- Proper UUID-based point IDs (fixes Qdrant validation errors)
- Systematic stages with progress tracking
- Comprehensive verification and scoring
- Error handling and graceful degradation
- Statistics and performance metrics

Data Sources:
1. Data.gov.in (Government Legal Datasets)
2. WorldLII/IndianLII (International Case Law)
3. Sample Legal Documents (Fallback/Reference Data)

Collections:
- statutes_vectors: Legal acts, statutes, government resources
- case_law_vectors: Court judgments and case law
- legal_taxonomy_vectors: Legal taxonomy, classifications, reports
- civic_process_vectors: Civic and administrative processes
- case_similarity_vectors: Case similarity data
"""

import logging
import sys
import time
import uuid
from typing import List, Dict, Tuple, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from qdrant_client.models import PointStruct

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
from database.qdrant_client import qdrant_manager
from utils.embeddings import get_embeddings


# =============================================================================
# STAGE 1: INITIALIZATION
# =============================================================================

def stage_1_initialize() -> Tuple[bool, Dict]:
    """Initialize all Qdrant collections."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 1: INITIALIZATION - Creating Qdrant Collections")
    logger.info("="*80)
    
    collections = [
        "statutes_vectors",
        "case_law_vectors",
        "legal_taxonomy_vectors",
        "case_similarity_vectors",
        "civic_process_vectors",
    ]
    
    stats = {"collections_created": 0, "collections_existing": 0}
    
    try:
        for collection in collections:
            info = qdrant_manager.get_collection_info(collection)
            if info:
                logger.info(f"  ✓ Collection '{collection}' already exists")
                stats["collections_existing"] += 1
            else:
                qdrant_manager.create_collection(collection)
                logger.info(f"  ✓ Created collection '{collection}'")
                stats["collections_created"] += 1
        
        logger.info(f"\n✓ STAGE 1 COMPLETE: {stats['collections_created']} created, "
                   f"{stats['collections_existing']} existing")
        return True, stats
    
    except Exception as e:
        logger.error(f"✗ STAGE 1 FAILED: {e}", exc_info=True)
        return False, stats


# =============================================================================
# STAGE 2: DATAGOV INGESTION
# =============================================================================

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start = max(0, end - overlap)
    return chunks


def ingest_datagov_dataset(api_url: str, collection_name: str = "statutes_vectors") -> Tuple[int, List[str]]:
    """Ingest a single Data.gov.in dataset."""
    ingested_count = 0
    errors = []
    
    try:
        logger.info(f"  Fetching dataset: {api_url}")
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        
        try:
            data = resp.json()
        except Exception:
            data = None
        
        resources = []
        if data:
            resources = data.get("resources") or []
        
        text_items = []
        provenance = []
        
        for r in resources:
            url = r.get("url")
            if not url:
                continue
            try:
                content = requests.get(url, timeout=30).text
                if content and len(content) > 100:
                    text_items.append(content)
                    provenance.append({
                        "source_url": url,
                        "resource_name": r.get("name", "unknown"),
                        "dataset_url": api_url
                    })
            except Exception as e:
                logger.debug(f"  Skipping resource {url}: {e}")
                continue
        
        if not text_items:
            logger.warning(f"  No resources found in dataset")
            return 0, []
        
        # Chunk and embed
        all_chunks = []
        chunk_metadata = []
        for text, prov in zip(text_items, provenance):
            chunks = chunk_text(text, chunk_size=800, overlap=150)
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "index": chunk_idx,
                    "provenance": prov
                })
        
        if not all_chunks:
            return 0, []
        
        logger.info(f"    Embedded {len(all_chunks)} chunks from {len(text_items)} resources")
        embeddings = get_embeddings(all_chunks)
        
        # Upsert with proper UUID-based point IDs
        batch_size = 64
        for i in range(0, len(all_chunks), batch_size):
            batch_end = min(i + batch_size, len(all_chunks))
            batch_chunks = all_chunks[i:batch_end]
            batch_embeddings = embeddings[i:batch_end]
            batch_metadata = chunk_metadata[i:batch_end]
            
            points = []
            for chunk, embedding, meta in zip(batch_chunks, batch_embeddings, batch_metadata):
                # Use UUID for point ID (fixes Qdrant validation errors)
                point_id = str(uuid.uuid4())
                
                payload = {
                    "source_name": "data.gov.in",
                    "source_url": meta["provenance"]["source_url"],
                    "resource_name": meta["provenance"]["resource_name"],
                    "dataset_url": meta["provenance"]["dataset_url"],
                    "ingestion_date": int(time.time()),
                    "chunk_index": meta["index"],
                    "chunk_text": chunk[:2000],
                    "jurisdiction": "india",
                }
                
                points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
            
            qdrant_manager.create_collection(collection_name)
            qdrant_manager.upsert_points(collection_name, points)
            ingested_count += len(points)
        
        logger.info(f"    ✓ Ingested {ingested_count} vectors to '{collection_name}'")
        return ingested_count, []
    
    except Exception as e:
        error_msg = f"Failed to ingest {api_url}: {str(e)}"
        logger.error(f"  ✗ {error_msg}")
        errors.append(error_msg)
        return 0, errors


def stage_2_datagov() -> Tuple[int, List[str]]:
    """Ingest datasets from Data.gov.in."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 2: DATA.GOV.IN INGESTION - Government Legal Datasets")
    logger.info("="*80)
    
    datasets = [
        "https://data.gov.in/api/3/action/package_show?id=justice-sector-statistics",
        "https://data.gov.in/api/3/action/package_show?id=courts-portal",
        "https://data.gov.in/api/3/action/package_show?id=constitutional-framework",
    ]
    
    total_ingested = 0
    all_errors = []
    
    for idx, dataset_url in enumerate(datasets, 1):
        logger.info(f"\nDataset {idx}/{len(datasets)}:")
        ingested, errors = ingest_datagov_dataset(dataset_url, "statutes_vectors")
        total_ingested += ingested
        all_errors.extend(errors)
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 2 COMPLETE: {total_ingested} total vectors ingested from Data.gov.in")
    return total_ingested, all_errors


# =============================================================================
# STAGE 3: WORLDLII INGESTION
# =============================================================================

def extract_text_from_html(html_bytes: bytes, chunk_size: int = 900) -> List[str]:
    """Extract and chunk text from HTML."""
    try:
        soup = BeautifulSoup(html_bytes, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()
        
        parts = soup.find_all(["pre", "div", "p", "article", "section"]) or [soup]
        text = "\n".join([p.get_text(separator=" ").strip() for p in parts])
        
        return chunk_text(text, chunk_size=chunk_size, overlap=200)
    except Exception as e:
        logger.error(f"HTML extraction failed: {e}")
        return []


def ingest_worldlii_case(case_url: str) -> Tuple[int, List[str]]:
    """Ingest a single WorldLII/IndianLII case."""
    errors = []
    
    try:
        logger.info(f"  Fetching case: {case_url}")
        resp = requests.get(case_url, timeout=30)
        resp.raise_for_status()
        
        chunks = extract_text_from_html(resp.content)
        
        if not chunks:
            logger.warning(f"  No text extracted from case")
            return 0, []
        
        logger.info(f"    Extracted {len(chunks)} chunks")
        embeddings = get_embeddings(chunks)
        
        # Upsert with proper UUID-based point IDs
        batch_size = 64
        ingested_count = 0
        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            batch_chunks = chunks[i:batch_end]
            batch_embeddings = embeddings[i:batch_end]
            
            points = []
            for chunk_idx, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                # Use UUID for point ID
                point_id = str(uuid.uuid4())
                
                payload = {
                    "source_name": "worldlii_indlii",
                    "source_url": case_url,
                    "ingestion_date": int(time.time()),
                    "chunk_index": chunk_idx,
                    "chunk_text": chunk[:2000],
                    "jurisdiction": "international",
                }
                
                points.append(PointStruct(id=point_id, vector=embedding, payload=payload))
            
            qdrant_manager.create_collection("case_law_vectors")
            qdrant_manager.upsert_points("case_law_vectors", points)
            ingested_count += len(points)
        
        logger.info(f"    ✓ Ingested {ingested_count} vectors")
        return ingested_count, []
    
    except Exception as e:
        error_msg = f"Failed to ingest {case_url}: {str(e)}"
        logger.error(f"  ✗ {error_msg}")
        return 0, [error_msg]


def stage_3_worldlii() -> Tuple[int, List[str]]:
    """Ingest case law from WorldLII/IndianLII."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 3: WORLDLII/INDLII INGESTION - Case Law")
    logger.info("="*80)
    
    cases = [
        "https://www.indlii.org/in/cases/INSC/2019/39.html",
        "https://www.indlii.org/in/cases/INSC/2017/87.html",
    ]
    
    total_ingested = 0
    all_errors = []
    
    for idx, case_url in enumerate(cases, 1):
        logger.info(f"\nCase {idx}/{len(cases)}:")
        ingested, errors = ingest_worldlii_case(case_url)
        total_ingested += ingested
        all_errors.extend(errors)
        time.sleep(1)  # Rate limiting
    
    logger.info(f"\n✓ STAGE 3 COMPLETE: {total_ingested} total vectors ingested from WorldLII")
    return total_ingested, all_errors


# =============================================================================
# STAGE 4: SAMPLE LEGAL DATA (FALLBACK)
# =============================================================================

def stage_4_sample_data() -> Tuple[int, List[str]]:
    """Ingest sample legal documents as fallback/reference data."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 4: SAMPLE LEGAL DATA - Reference Documents")
    logger.info("="*80)
    
    sample_docs = [
        {
            "title": "Right to Information Act 2005",
            "content": """The Right to Information Act, 2005 is an Act of the Parliament of India 
to provide for setting out the practical regime of right to information for citizens. It replaces 
the Freedom of Information Act, 2002. According to the act, any Indian citizen can request 
information from a "public authority" (a body of Government at the Union, State or local level). 
The Act imposes a duty on public authorities to maintain and computerize their records. 
Every public authority should have a Public Information Officer to monitor requests. 
Requests can be filed in writing and fees are minimal.""",
            "source": "legal_reference",
            "category": "statutes"
        },
        {
            "title": "Indian Penal Code Overview",
            "content": """The Indian Penal Code, 1860 is the main criminal code in India. 
It defines offences and prescribes punishments for crimes. The IPC is divided into 23 chapters 
covering General Principles, Punishment, General Exceptions, General Principles Governing 
Liability, Act of Persons Bound by Law, Act of Persons Excepted from Criminal Responsibility, 
General Principles Respecting Defences, Of Hurt, Of Wrongful Restraint and Wrongful Confinement, 
Of Criminal Force and Assault, Of Theft, Of Extortion and Robbery, Of Criminal Misappropriation 
and Criminal Breach of Trust, Of Cheating and Fraudulent Dealing, Of Offences Against Religion, 
Of Offences Relating to Elections, Of Contempt of Lawful Authority, Of False Evidence, 
Of Offences Against Public Health, Safety, Convenience, Decency and Morals, Of Offences 
Relating to Elections, Of Offences by or Relating to Elections, Of Contempt of Courts and 
Public Servants, General Exceptions, and Punishments.""",
            "source": "legal_reference",
            "category": "statutes"
        },
        {
            "title": "Code of Civil Procedure Overview",
            "content": """The Code of Civil Procedure, 1908 (CPC) governs the procedure for 
administration of the civil law in courts. It contains procedural laws that apply in district courts, 
high courts, and the Supreme Court. The CPC is divided into sections covering applications of the code, 
courts and officers, jurisdiction, limitation, alternative dispute resolution, parties and legal 
representation, suits, summons and notices, appearance, plaint, written statement and defence, 
examination of parties, examination of witnesses, expert evidence, opinion of third parties, 
production and inspection of documents, circumstantial evidence, judgment and orders, appeals, 
review and revision, reference, arbitration, transfer, trial, preliminary decrees, determination 
of liability, execution, and other miscellaneous provisions.""",
            "source": "legal_reference",
            "category": "statutes"
        },
        {
            "title": "Constitution of India - Part III Rights",
            "content": """Part III of the Constitution of India contains the Fundamental Rights 
granted to all Indians. These include the right to equality, freedom of speech and expression, 
freedom of assembly, freedom of association, freedom of movement, freedom of residence and 
settlement, freedom of profession trade or business, protection regarding conviction for offences, 
protection against retrospective laws, abolition of slavery, suppression of traffic in human beings 
and forced labour. These rights are enforceable in courts and cannot be suspended except during 
national emergencies. The Fundamental Rights are subject to reasonable restrictions in the interest 
of sovereignty, security, order, morality, and protection of public health.""",
            "source": "legal_reference",
            "category": "statutes"
        },
        {
            "title": "Landmark Judgment - Privacy Rights",
            "content": """In a landmark judgment, the Supreme Court recognized the right to privacy 
as a fundamental right under the Indian Constitution. The judgment affirmed that privacy is 
intrinsic to liberty and the dignity of the individual. The court held that the right to privacy 
is not a standalone right but a facet of the broader right to life and liberty guaranteed under 
Article 21 of the Constitution. The judgment recognized various dimensions of privacy including 
personal privacy, informational privacy, and decisional privacy. The court also established a 
proportionality test for restrictions on privacy rights, requiring that any restriction must be 
prescribed by law, pursue a legitimate state interest, and be necessary and proportionate.""",
            "source": "legal_reference",
            "category": "case_law"
        },
        {
            "title": "Judicial Process - Filing a Petition",
            "content": """Filing a petition before a court is a fundamental right of every citizen. 
A petitioner can approach the court with any grievance or claim. To file a petition, one must have 
locus standi (legal interest or standing to sue). The petition must contain facts supported by an 
affidavit. The petitioner must clearly state the relief sought. Petitions can be filed for various 
purposes including seeking writs of habeas corpus, mandamus, prohibition, quo warranto, and 
certiorari. The Supreme Court has both original and appellate jurisdiction. District courts have 
civil and criminal jurisdiction in their areas. Petitions must be filed through an advocate unless 
permitted otherwise by law.""",
            "source": "legal_reference",
            "category": "civic_process"
        }
    ]
    
    ingested_count = 0
    errors = []
    
    try:
        all_chunks = []
        chunk_metadata = []
        
        for doc in sample_docs:
            chunks = chunk_text(doc["content"], chunk_size=600, overlap=100)
            for chunk_idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({
                    "title": doc["title"],
                    "source": doc["source"],
                    "category": doc["category"],
                    "chunk_idx": chunk_idx
                })
        
        logger.info(f"  Embedding {len(all_chunks)} chunks from {len(sample_docs)} documents")
        embeddings = get_embeddings(all_chunks)
        
        # Determine target collection based on category
        collection_mapping = {
            "statutes": "statutes_vectors",
            "case_law": "case_law_vectors",
            "civic_process": "civic_process_vectors"
        }
        
        # Upsert with proper UUID-based point IDs
        for chunk, embedding, meta in zip(all_chunks, embeddings, chunk_metadata):
            point_id = str(uuid.uuid4())
            
            payload = {
                "source_name": meta["source"],
                "title": meta["title"],
                "category": meta["category"],
                "ingestion_date": int(time.time()),
                "chunk_index": meta["chunk_idx"],
                "chunk_text": chunk[:2000],
                "jurisdiction": "india",
            }
            
            # Determine collection
            collection = collection_mapping.get(meta["category"], "legal_taxonomy_vectors")
            
            points = [PointStruct(id=point_id, vector=embedding, payload=payload)]
            qdrant_manager.create_collection(collection)
            qdrant_manager.upsert_points(collection, points)
            ingested_count += 1
        
        logger.info(f"  ✓ Ingested {ingested_count} vectors from sample data")
        return ingested_count, []
    
    except Exception as e:
        error_msg = f"Failed to ingest sample data: {str(e)}"
        logger.error(f"  ✗ {error_msg}")
        return 0, [error_msg]


# =============================================================================
# STAGE 5: VERIFICATION & SCORING
# =============================================================================

def stage_5_verification() -> Dict:
    """Verify ingestion and generate statistics."""
    logger.info("\n" + "="*80)
    logger.info("STAGE 5: VERIFICATION & SCORING - Checking Qdrant Data")
    logger.info("="*80)
    
    collections = [
        "statutes_vectors",
        "case_law_vectors",
        "legal_taxonomy_vectors",
        "case_similarity_vectors",
        "civic_process_vectors",
    ]
    
    stats = {
        "total_vectors": 0,
        "collection_stats": {},
        "quality_score": 0.0,
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
                logger.warning(f"  ! {collection}: No data")
        except Exception as e:
            logger.warning(f"  ! {collection}: {e}")
            stats["collection_stats"][collection] = 0
    
    # Calculate quality score
    # Score based on: vectors ingested, data distribution, collection coverage
    vectors_score = min(100, (stats["total_vectors"] / 100) * 100)  # Max 100 at 100 vectors
    collections_score = (len([c for c in stats["collection_stats"].values() if c > 0]) 
                        / len(collections)) * 100
    distribution_score = (min(100, sum(1 for c in stats["collection_stats"].values() 
                             if c > 10)) / len(collections)) * 100
    
    stats["quality_score"] = (vectors_score * 0.5 + collections_score * 0.3 
                             + distribution_score * 0.2)
    
    logger.info(f"\n📊 VERIFICATION SCORES:")
    logger.info(f"  • Vectors Ingested: {vectors_score:.1f}/100")
    logger.info(f"  • Collections Used: {collections_score:.1f}/100")
    logger.info(f"  • Data Distribution: {distribution_score:.1f}/100")
    logger.info(f"  • OVERALL QUALITY: {stats['quality_score']:.1f}/100")
    
    logger.info(f"\n✓ STAGE 5 COMPLETE: {stats['total_vectors']:,} total vectors verified")
    return stats


# =============================================================================
# MAIN ORCHESTRATION
# =============================================================================

def main():
    """Execute comprehensive ingestion pipeline."""
    logger.info("\n" + "█"*80)
    logger.info("█" + " "*78 + "█")
    logger.info("█" + "  NYAYAAI - COMPREHENSIVE CONNECTOR DATA INGESTION (FINAL VERSION)".center(78) + "█")
    logger.info("█" + " "*78 + "█")
    logger.info("█"*80)
    
    start_time = time.time()
    stage_results = {}
    
    try:
        # STAGE 1: Initialize
        success, init_stats = stage_1_initialize()
        if not success:
            logger.error("Failed to initialize. Aborting.")
            sys.exit(1)
        stage_results["initialization"] = init_stats
        
        # STAGE 2: Data.gov.in
        datagov_count, datagov_errors = stage_2_datagov()
        stage_results["datagov"] = {"ingested": datagov_count, "errors": datagov_errors}
        
        # STAGE 3: WorldLII
        worldlii_count, worldlii_errors = stage_3_worldlii()
        stage_results["worldlii"] = {"ingested": worldlii_count, "errors": worldlii_errors}
        
        # STAGE 4: Sample Data
        sample_count, sample_errors = stage_4_sample_data()
        stage_results["sample_data"] = {"ingested": sample_count, "errors": sample_errors}
        
        # STAGE 5: Verification
        verification_stats = stage_5_verification()
        stage_results["verification"] = verification_stats
        
        # FINAL SUMMARY
        logger.info("\n" + "="*80)
        logger.info("FINAL INGESTION SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\n📋 SOURCES INGESTED:")
        logger.info(f"  • Data.gov.in:  {datagov_count:,} vectors")
        logger.info(f"  • WorldLII:     {worldlii_count:,} vectors")
        logger.info(f"  • Sample Data:  {sample_count:,} vectors")
        logger.info(f"  " + "─"*35)
        logger.info(f"  • TOTAL:        {verification_stats['total_vectors']:,} vectors")
        
        logger.info(f"\n📦 COLLECTIONS STATUS:")
        for collection, count in verification_stats["collection_stats"].items():
            status = "✓" if count > 0 else "○"
            logger.info(f"  {status} {collection}: {count:,} vectors")
        
        logger.info(f"\n🎯 QUALITY METRICS:")
        logger.info(f"  • Overall Quality Score: {verification_stats['quality_score']:.1f}/100")
        
        elapsed = time.time() - start_time
        logger.info(f"\n⏱️  PERFORMANCE:")
        logger.info(f"  • Total Time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        logger.info(f"  • Vectors/sec: {verification_stats['total_vectors']/elapsed:.1f}")
        
        logger.info(f"\n✅ INGESTION PIPELINE COMPLETE!")
        logger.info("="*80)
        
        return 0
    
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}", exc_info=True)
        logger.info("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
