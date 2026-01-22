"""Connector for WorldLII/AsianLII/IndianLII case collections ingestion."""
import logging
from typing import Optional

from connectors.helpers import generic_ingest_url

logger = logging.getLogger(__name__)


def ingest_case(url: str, collection_name: str = "case_law_vectors") -> bool:
    """Ingest a case law page from WorldLII/AsianLII/IndianLII.

    These sites host HTML judgments that can be parsed and ingested using the
    generic ingestion helper.
    """
    logger.info(f"Ingesting WorldLII case: {url}")
    return generic_ingest_url(url, collection_name, source_name="worldlii")


if __name__ == "__main__":
    example = "https://www.worldlii.org/int/cases/INSC/1997/3011.html"
    ingest_case(example)
