"""Connector for Data.gov.in datasets and resources.

This module can fetch a dataset JSON (CKAN-style) from Data.gov.in and ingest
text resources (HTML, text, PDF links) into the `statutes_vectors` collection
or a collection you provide.
"""
import logging
import time
from typing import List

import requests
from qdrant_client.models import PointStruct

from utils.embeddings import get_embeddings
from database.qdrant_db import qdrant_manager
from connectors.helpers import generic_ingest_url

logger = logging.getLogger(__name__)


def ingest_from_datagov_dataset(api_dataset_url: str, collection_name: str = "statutes_vectors") -> bool:
    """Fetch CKAN-style dataset JSON and ingest its textual resources.

    Example dataset URL: https://data.gov.in/sites/default/files/dataset.json
    """
    logger.info(f"Fetching dataset metadata: {api_dataset_url}")
    try:
        resp = requests.get(api_dataset_url, timeout=30)
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            data = None
    except Exception as e:
        logger.error(f"Failed to fetch dataset JSON: {e}")
        return False
    resources = []
    if data:
        resources = data.get("resources") or []
    else:
        # fallback: parse HTML page and try to find resource links
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("http") or href.lower().endswith((".pdf", ".csv", ".txt", ".html")):
                    resources.append({"url": href, "name": a.get_text(strip=True) or href})
        except Exception:
            resources = []
    text_items: List[str] = []
    provenance: List[dict] = []

    for r in resources:
        url = r.get("url")
        if not url:
            continue
        try:
            content = requests.get(url, timeout=30).text
        except Exception:
            logger.debug(f"Skipping non-text resource: {url}")
            continue

        # Add as one item per resource (caller can re-chunk)
        text_items.append(content)
        provenance.append({"source_url": url, "resource_name": r.get("name")})

    if not text_items:
        logger.info("No textual resources found in dataset")
        return False

    # Chunking approach: simple split by paragraphs and ingest in batches
    batch_size = 64
    for i in range(0, len(text_items), batch_size):
        batch = text_items[i : i + batch_size]
        embeddings = get_embeddings(batch)
        points = []
        for j, (text, prov) in enumerate(zip(batch, provenance[i : i + batch_size])):
            pid = f"datagov-{int(time.time())}-{i+j}"
            payload = {
                "source_name": "data.gov.in",
                "source_url": prov.get("source_url"),
                "resource_name": prov.get("resource_name"),
                "ingestion_date": int(time.time()),
                "chunk_text": text[:2000],
                "jurisdiction": "india",
            }
            points.append(PointStruct(id=pid, vector=embeddings[j], payload=payload))

        qdrant_manager.create_collection(collection_name)
        qdrant_manager.upsert_points(collection_name, points)

    logger.info("Completed ingest from data.gov dataset")
    return True
