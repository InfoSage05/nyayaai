"""Connector to ingest Law Commission of India reports (taxonomy & reference)."""
import logging
from typing import Optional

from connectors.helpers import generic_ingest_url

logger = logging.getLogger(__name__)


def ingest_report(url: str, collection_name: str = "legal_taxonomy_vectors") -> bool:
    """Ingest a Law Commission report or similar government report into Qdrant.

    The Law Commission site typically hosts PDF reports; this function uses the
    generic ingestion helper which includes a PDF/text extractor and OCR fallback.
    """
    logger.info(f"Ingesting Law Commission report: {url}")
    return generic_ingest_url(url, collection_name, source_name="law_commission_of_india")


if __name__ == "__main__":
    # quick test example (replace with real URL)
    example = "https://lawcommissionofindia.nic.in/reports/rep200.pdf"
    ingest_report(example)
