"""Script to ingest sample legal data into Qdrant collections."""
import logging
from typing import List, Dict, Any
from qdrant_client.models import PointStruct
import uuid

from .qdrant_client import qdrant_manager
from utils.embeddings import get_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample Legal Taxonomy Data
SAMPLE_TAXONOMY = [
    {
        "text": "constitutional law fundamental rights article 14 equality before law",
        "domain": "constitutional_law",
        "description": "Constitutional law covering fundamental rights and equality"
    },
    {
        "text": "criminal law FIR police arrest bail procedure",
        "domain": "criminal_law",
        "description": "Criminal law procedures including FIR, arrest, and bail"
    },
    {
        "text": "civil law contract breach damages compensation",
        "domain": "civil_law",
        "description": "Civil law covering contracts, breaches, and damages"
    },
    {
        "text": "family law marriage divorce custody maintenance",
        "domain": "family_law",
        "description": "Family law including marriage, divorce, and custody"
    },
    {
        "text": "property law land ownership title possession",
        "domain": "property_law",
        "description": "Property law covering land, ownership, and titles"
    },
    {
        "text": "labor law employment wage termination worker rights",
        "domain": "labor_law",
        "description": "Labor law covering employment, wages, and worker rights"
    },
    {
        "text": "consumer protection defective product refund warranty",
        "domain": "consumer_protection",
        "description": "Consumer protection laws and rights"
    },
    {
        "text": "environmental law pollution forest wildlife protection",
        "domain": "environmental_law",
        "description": "Environmental protection laws"
    },
    {
        "text": "civic rights voting citizen right to information RTI",
        "domain": "civic_rights",
        "description": "Civic rights including voting and information access"
    }
]


# Sample Statutes Data
SAMPLE_STATUTES = [
    {
        "text": "Right to Information Act 2005 Section 4 Every public authority shall maintain all its records duly catalogued and indexed",
        "title": "Right to Information Act, 2005 - Section 4",
        "section": "Section 4",
        "act_name": "Right to Information Act, 2005",
        "content": "Every public authority shall maintain all its records duly catalogued and indexed in a manner and the form which facilitates the right to information under this Act",
        "domain": "civic_rights",
        "jurisdiction": "india"
    },
    {
        "text": "Indian Penal Code Section 375 Rape A man is said to commit rape",
        "title": "Indian Penal Code - Section 375",
        "section": "Section 375",
        "act_name": "Indian Penal Code, 1860",
        "content": "A man is said to commit rape if he has sexual intercourse with a woman under circumstances falling under any of the seven descriptions",
        "domain": "criminal_law",
        "jurisdiction": "india"
    },
    {
        "text": "Consumer Protection Act 2019 Section 2 Defective product means any good which has any fault imperfection",
        "title": "Consumer Protection Act, 2019 - Section 2",
        "section": "Section 2",
        "act_name": "Consumer Protection Act, 2019",
        "content": "Defective product means any good which has any fault, imperfection or shortcoming in the quality, quantity, potency, purity or standard",
        "domain": "consumer_protection",
        "jurisdiction": "india"
    },
    {
        "text": "Hindu Marriage Act 1955 Section 13 Divorce grounds for divorce",
        "title": "Hindu Marriage Act, 1955 - Section 13",
        "section": "Section 13",
        "act_name": "Hindu Marriage Act, 1955",
        "content": "Any marriage solemnized, whether before or after the commencement of this Act, may, on a petition presented by either the husband or the wife, be dissolved by a decree of divorce",
        "domain": "family_law",
        "jurisdiction": "india"
    },
    {
        "text": "Constitution of India Article 14 Equality before law equal protection of laws",
        "title": "Constitution of India - Article 14",
        "section": "Article 14",
        "act_name": "Constitution of India",
        "content": "The State shall not deny to any person equality before the law or the equal protection of the laws within the territory of India",
        "domain": "constitutional_law",
        "jurisdiction": "india"
    }
]


# Sample Case Law Data
SAMPLE_CASES = [
    {
        "text": "Maneka Gandhi v Union of India 1978 right to travel passport fundamental right",
        "case_name": "Maneka Gandhi v. Union of India",
        "court": "Supreme Court of India",
        "year": "1978",
        "summary": "Landmark case establishing that the right to travel abroad is a fundamental right under Article 21",
        "key_points": ["Right to travel", "Article 21", "Due process", "Fundamental rights"],
        "citation": "AIR 1978 SC 597",
        "domain": "constitutional_law"
    },
    {
        "text": "Vishaka v State of Rajasthan 1997 sexual harassment workplace guidelines",
        "case_name": "Vishaka v. State of Rajasthan",
        "court": "Supreme Court of India",
        "year": "1997",
        "summary": "Case establishing guidelines for prevention of sexual harassment at workplace",
        "key_points": ["Sexual harassment", "Workplace safety", "Gender equality", "Prevention guidelines"],
        "citation": "AIR 1997 SC 3011",
        "domain": "labor_law"
    },
    {
        "text": "MC Mehta v Union of India 1987 environmental protection polluter pays principle",
        "case_name": "MC Mehta v. Union of India",
        "court": "Supreme Court of India",
        "year": "1987",
        "summary": "Environmental case establishing polluter pays principle and environmental protection",
        "key_points": ["Environmental protection", "Polluter pays", "Public interest litigation", "Article 21"],
        "citation": "AIR 1987 SC 1086",
        "domain": "environmental_law"
    }
]


# Sample Civic Process Data
SAMPLE_CIVIC_PROCESSES = [
    {
        "text": "How to file RTI application Right to Information procedure steps",
        "action": "File RTI Application",
        "description": "Process to file a Right to Information application to access government records",
        "steps": [
            "Identify the public authority",
            "Draft RTI application with specific questions",
            "Pay application fee (Rs. 10)",
            "Submit to Public Information Officer",
            "Receive response within 30 days"
        ],
        "authority": "Central/State Public Information Officer",
        "required_documents": ["RTI application form", "Fee payment proof", "Identity proof"],
        "timeline": "30 days",
        "cost": "Rs. 10",
        "domain": "civic_rights"
    },
    {
        "text": "How to file consumer complaint defective product refund",
        "action": "File Consumer Complaint",
        "description": "Process to file a complaint for defective products or services",
        "steps": [
            "Gather evidence (receipt, photos, documents)",
            "File complaint with Consumer Forum",
            "Pay required fees",
            "Attend hearings",
            "Receive order"
        ],
        "authority": "District/State/National Consumer Disputes Redressal Commission",
        "required_documents": ["Purchase receipt", "Product photos", "Complaint letter", "Evidence"],
        "timeline": "90-180 days",
        "cost": "Varies by forum",
        "domain": "consumer_protection"
    },
    {
        "text": "How to file FIR First Information Report police station procedure",
        "action": "File FIR",
        "description": "Process to file a First Information Report at a police station",
        "steps": [
            "Go to nearest police station",
            "Provide oral or written complaint",
            "Police records complaint in FIR register",
            "Obtain FIR copy",
            "Follow up on investigation"
        ],
        "authority": "Police Station",
        "required_documents": ["Identity proof", "Incident details", "Witnesses if any"],
        "timeline": "Immediate",
        "cost": "Free",
        "domain": "criminal_law"
    }
]


def ingest_taxonomy():
    """Ingest legal taxonomy data."""
    logger.info("Ingesting legal taxonomy data...")
    
    texts = [item["text"] for item in SAMPLE_TAXONOMY]
    embeddings = get_embeddings(texts)
    
    points = []
    for i, (item, embedding) in enumerate(zip(SAMPLE_TAXONOMY, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": item["text"],
                "domain": item["domain"],
                "description": item["description"],
                "source": "sample_data",
                "agent_name": "ingestion",
                "confidence": 1.0
            }
        )
        points.append(point)
    
    success = qdrant_manager.upsert_points("legal_taxonomy_vectors", points)
    logger.info(f"✓ Ingested {len(points)} taxonomy entries")
    return success


def ingest_statutes():
    """Ingest statutes data."""
    logger.info("Ingesting statutes data...")
    
    texts = [item["text"] for item in SAMPLE_STATUTES]
    embeddings = get_embeddings(texts)
    
    points = []
    for i, (item, embedding) in enumerate(zip(SAMPLE_STATUTES, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "title": item["title"],
                "section": item["section"],
                "act_name": item["act_name"],
                "content": item["content"],
                "text": item["text"],
                "domain": item["domain"],
                "jurisdiction": item["jurisdiction"],
                "source": "sample_data",
                "agent_name": "ingestion",
                "confidence": 1.0
            }
        )
        points.append(point)
    
    success = qdrant_manager.upsert_points("statutes_vectors", points)
    logger.info(f"✓ Ingested {len(points)} statute entries")
    return success


def ingest_cases():
    """Ingest case law data."""
    logger.info("Ingesting case law data...")
    
    texts = [item["text"] for item in SAMPLE_CASES]
    embeddings = get_embeddings(texts)
    
    points = []
    for i, (item, embedding) in enumerate(zip(SAMPLE_CASES, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "case_name": item["case_name"],
                "court": item["court"],
                "year": item["year"],
                "summary": item["summary"],
                "key_points": item["key_points"],
                "citation": item["citation"],
                "text": item["text"],
                "domain": item["domain"],
                "source": "sample_data",
                "agent_name": "ingestion",
                "confidence": 1.0
            }
        )
        points.append(point)
    
    success = qdrant_manager.upsert_points("case_law_vectors", points)
    logger.info(f"✓ Ingested {len(points)} case law entries")
    return success


def ingest_civic_processes():
    """Ingest civic process data."""
    logger.info("Ingesting civic process data...")
    
    texts = [item["text"] for item in SAMPLE_CIVIC_PROCESSES]
    embeddings = get_embeddings(texts)
    
    points = []
    for i, (item, embedding) in enumerate(zip(SAMPLE_CIVIC_PROCESSES, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "action": item["action"],
                "description": item["description"],
                "steps": item["steps"],
                "authority": item["authority"],
                "required_documents": item["required_documents"],
                "timeline": item["timeline"],
                "cost": item["cost"],
                "text": item["text"],
                "domain": item["domain"],
                "source": "sample_data",
                "agent_name": "ingestion",
                "confidence": 1.0
            }
        )
        points.append(point)
    
    success = qdrant_manager.upsert_points("civic_process_vectors", points)
    logger.info(f"✓ Ingested {len(points)} civic process entries")
    return success


def ingest_all():
    """Ingest all sample data."""
    logger.info("Starting sample data ingestion...")
    
    results = {
        "taxonomy": ingest_taxonomy(),
        "statutes": ingest_statutes(),
        "cases": ingest_cases(),
        "civic_processes": ingest_civic_processes()
    }
    
    logger.info("Sample data ingestion complete!")
    return results


if __name__ == "__main__":
    ingest_all()
