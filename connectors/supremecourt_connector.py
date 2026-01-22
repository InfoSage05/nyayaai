"""Connector for Supreme Court of India judgments.

This connector downloads a judgment HTML/PDF, extracts main text, chunks, embeds, and upserts
to the `case_law_vectors` collection by default.
"""
import hashlib
import logging
import time
from typing import List

import requests
from bs4 import BeautifulSoup
from qdrant_client.models import PointStruct

from utils.embeddings import get_embeddings
from database.qdrant_client import qdrant_manager
from connectors.helpers import generic_ingest_url

logger = logging.getLogger(__name__)


def _download(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def _extract_text(html_bytes: bytes) -> str:
    soup = BeautifulSoup(html_bytes, "html.parser")
    for s in soup(["script", "style"]):
        s.decompose()
    # Supreme Court pages often put judgments inside <div class="JUDGMENT"> or <pre>
    parts = soup.find_all(["pre", "div", "p"]) or [soup]
    text = "\n".join([p.get_text(separator=" ").strip() for p in parts])
    return text


def _chunk(text: str, chunk_size: int = 900, overlap: int = 200) -> List[str]:
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


def _make_id(url: str, idx: int, snippet: str) -> str:
    return hashlib.sha1(f"{url}|{idx}|{snippet[:120]}".encode("utf-8")).hexdigest()


def ingest_judgment(url: str, collection_name: str = "case_law_vectors") -> bool:
    logger.info(f"Ingesting judgment: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.content
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

    # Check for PDF link on the page (prefer canonical PDF)
    try:
        soup = BeautifulSoup(data, "html.parser")
        pdf_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().endswith(".pdf") or "pdf" in href.lower():
                pdf_link = href
                break
        if pdf_link:
            if pdf_link.startswith("/"):
                from urllib.parse import urljoin

                pdf_link = urljoin(url, pdf_link)
            logger.info(f"Found PDF link; delegating to generic ingest: {pdf_link}")
            return generic_ingest_url(pdf_link, collection_name, source_name="supreme_court_of_india")
    except Exception:
        pass

    text = _extract_text(data)
    if not text or len(text) < 200:
        logger.error("Extracted text too short; aborting")
        return False

    chunks = _chunk(text)
    if not chunks:
        logger.error("No chunks produced")
        return False

    batch_size = 64
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embeddings = get_embeddings(batch)
        points = []
        for j, (chunk, emb) in enumerate(zip(batch, embeddings)):
            idx = i + j
            pid = _make_id(url, idx, chunk)
            payload = {
                "source_name": "supreme_court_of_india",
                "source_url": url,
                "ingestion_date": int(time.time()),
                "chunk_index": idx,
                "chunk_text": chunk,
                "jurisdiction": "india",
            }
            points.append(PointStruct(id=pid, vector=emb, payload=payload))

        qdrant_manager.create_collection(collection_name)
        qdrant_manager.upsert_points(collection_name, points)

    logger.info(f"Finished ingesting judgment {url}")
    return True
