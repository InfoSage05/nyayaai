"""Shared helper utilities for connectors: download, extraction, OCR fallback, generic ingestion."""
import logging
import time
from typing import List, Optional

import requests
from qdrant_client.models import PointStruct

from database.qdrant_db import qdrant_manager
from utils.embeddings import get_embeddings

logger = logging.getLogger(__name__)


def download_bytes(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def extract_text_from_html_bytes(html_bytes: bytes) -> str:
    try:
        from bs4 import BeautifulSoup
    except Exception:
        raise

    soup = BeautifulSoup(html_bytes, "html.parser")
    for s in soup(["script", "style"]):
        s.decompose()
    parts = soup.find_all(["p", "div", "pre", "section"]) or [soup]
    text = "\n".join([p.get_text(separator=" ").strip() for p in parts])
    return text


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf; if empty, attempt OCR via pdf2image + pytesseract.

    Notes:
    - OCR requires `pdf2image` and `pytesseract` and external binaries (poppler, tesseract).
    - This function falls back gracefully if OCR dependencies are missing.
    """
    text = ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_bytes)
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            text += page_text + "\n"
    except Exception:
        # pypdf may accept bytes path; try reading via temporary file approach in callers
        text = ""

    if text and len(text) > 200:
        return text

    # Attempt OCR fallback
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        from PIL import Image
    except Exception as e:
        logger.debug(f"OCR dependencies not available: {e}")
        return text

    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_text = []
        for img in images:
            try:
                page_text = pytesseract.image_to_string(img)
            except Exception:
                page_text = ""
            ocr_text.append(page_text)
        combined = "\n".join(ocr_text)
        return combined
    except Exception as e:
        logger.debug(f"PDF->image OCR failed: {e}")
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


def generic_ingest_url(
    url: str,
    collection_name: str,
    source_name: Optional[str] = None,
    chunk_size: int = 800,
    batch_size: int = 64,
) -> bool:
    """Generic ingest: download URL, extract text (HTML/PDF), chunk, embed, upsert to Qdrant.

    Returns True on success.
    """
    logger.info(f"Generic ingest for {url} -> {collection_name}")
    try:
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return False

    content_type = resp.headers.get("Content-Type", "")
    content = resp.content

    text = ""
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        text = extract_text_from_pdf_bytes(content)
    else:
        try:
            text = extract_text_from_html_bytes(content)
        except Exception:
            # fallback to PDF extractor
            text = extract_text_from_pdf_bytes(content)

    if not text or len(text) < 200:
        logger.error("Extracted text empty or too short")
        return False

    chunks = chunk_text(text, chunk_size=chunk_size)
    if not chunks:
        logger.error("No chunks created")
        return False

    # Prepare and upsert in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embeddings = get_embeddings(batch)
        points = []
        for j, (chunk, emb) in enumerate(zip(batch, embeddings)):
            idx = i + j
            pid = f"{int(time.time())}-{idx}"
            payload = {
                "source_name": source_name or "generic",
                "source_url": url,
                "ingestion_date": int(time.time()),
                "chunk_index": idx,
                "chunk_text": chunk,
            }
            points.append(PointStruct(id=pid, vector=emb, payload=payload))

        qdrant_manager.create_collection(collection_name)
        qdrant_manager.upsert_points(collection_name, points)

    logger.info(f"Generic ingest complete for {url}")
    return True
