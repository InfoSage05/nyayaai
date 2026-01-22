"""Embedding utilities using SentenceTransformers."""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

# Global embedding model (loaded once)
_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get or load the embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully")
    return _embedding_model


def get_embeddings(texts: Union[str, List[str]]) -> List[List[float]]:
    """Generate embeddings for text(s).
    
    Args:
        texts: Single string or list of strings
        
    Returns:
        List of embedding vectors (list of floats)
    """
    model = get_embedding_model()
    
    if isinstance(texts, str):
        texts = [texts]
    
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def get_embedding(text: str) -> List[float]:
    """Generate embedding for a single text.
    
    Args:
        text: Input text string
        
    Returns:
        Embedding vector (list of floats)
    """
    embeddings = get_embeddings(text)
    return embeddings[0]
