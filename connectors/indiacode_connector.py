"""Connector to fetch acts/sections from IndiaCode or similar sources.

This module provides a lightweight downloader/parser that extracts text
from HTML or PDF, chunks it, embeds by calling `utils.embeddings.get_embeddings`,
and upserts vectors to Qdrant via `database.qdrant_client.qdrant_manager`.

Usage:
    from connectors.indiacode_connector import ingest_act_from_url
    ingest_act_from_url("https://www.indiacode.nic.in/...", collection_name="statutes_vectors")
"""
import hashlib
import logging
import time
import uuid
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from qdrant_client.models import PointStruct

from utils.embeddings import get_embeddings
from database.qdrant_db import qdrant_manager
from connectors.helpers import generic_ingest_url

logger = logging.getLogger(__name__)


def _download(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def _extract_text_from_html(html_bytes: bytes) -> str:
    soup = BeautifulSoup(html_bytes, "html.parser")
    # Remove scripts/styles
    for s in soup(["script", "style"]):
        s.decompose()
    text = "\n".join([p.get_text(separator=" ").strip() for p in soup.find_all(["p", "div", "pre", "section"])])
    return text


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
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


def _make_chunk_id(source_url: str, idx: int, chunk_text: str) -> str:
    h = hashlib.sha1(f"{source_url}|{idx}|{chunk_text[:120]}".encode("utf-8")).hexdigest()
    return h


def ingest_act_from_url(url: str, collection_name: str = "statutes_vectors", chunk_size: int = 800):
    """Fetch an act page (HTML or PDF) from `url`, extract text, chunk, embed, and upsert to Qdrant.

    This improved implementation prefers a canonical PDF when present (IndiaCode uses
    PDF/bitstream links) and delegates PDF ingestion to the generic helper which
    includes OCR fallback. If no PDF is found, it extracts HTML text and ingests.
    """
    logger.info(f"Ingesting act from: {url}")

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return False

    soup = BeautifulSoup(resp.content, "html.parser")
    pdf_link = None
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf") or "bitstream" in href.lower():
            pdf_link = href
            break

    if pdf_link:
        if pdf_link.startswith("/"):
            from urllib.parse import urljoin

            pdf_link = urljoin(url, pdf_link)
        logger.info(f"Found PDF link; delegating to generic ingest: {pdf_link}")
        return generic_ingest_url(pdf_link, collection_name, source_name="indiacode")

    # No PDF found; fall back to HTML extraction and ingest
    text = _extract_text_from_html(resp.content)
    if not text or len(text) < 200:
        logger.error("No extractable text found on page")
        return False

    chunks = chunk_text(text, chunk_size=chunk_size)
    if not chunks:
        logger.error("No chunks created")
        return False

    batch_size = 64
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embeddings = get_embeddings(batch)
        points = []
        for idx, (chunk, emb) in enumerate(zip(batch, embeddings)):
            chunk_index = i + idx
            pid = _make_chunk_id(url, chunk_index, chunk)
            payload = {
                "source_name": "indiacode",
                "source_url": url,
                "ingestion_date": int(time.time()),
                "chunk_index": chunk_index,
                "chunk_text": chunk,
                "jurisdiction": "india",
            }
            points.append(PointStruct(id=pid, vector=emb, payload=payload))

        qdrant_manager.create_collection(collection_name)
        qdrant_manager.upsert_points(collection_name, points)

    logger.info(f"Completed ingest for {url}")
    return True
