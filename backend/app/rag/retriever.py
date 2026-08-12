"""
Hybrid Retriever Module
Executes entity-aware vector search with metadata pre-filtering and score thresholding.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.rag.vector_store import vector_store_manager
from app.utils.logger import get_logger

logger = get_logger("rag.retriever")

def retrieve_context(
    query: str,
    scheme_slug: str | None = None,
    fact_type: str | None = None,
    top_k: int = 3,
    confidence_threshold: float = settings.CONFIDENCE_THRESHOLD
) -> dict:
    """
    Retrieves candidate context chunks from the vector store matching the query and metadata filters.
    """
    logger.info(f"Executing hybrid retrieval for query: '{query}' (scheme_slug={scheme_slug}, fact_type={fact_type})")

    # 1. First search attempt with scheme_slug and fact_type filter
    chunks = vector_store_manager.search(
        query=query,
        scheme_slug=scheme_slug,
        fact_type=fact_type,
        top_k=top_k,
        score_threshold=0.0
    )

    # If exact metadata match occurred, boost chunk confidence score
    if chunks and scheme_slug and fact_type:
        for c in chunks:
            if c["metadata"].get("scheme_slug") == scheme_slug and c["metadata"].get("fact_type") == fact_type:
                c["score"] = max(c["score"], 0.95)

    # 2. Fallback search attempt if specific fact_type returned no results
    if not chunks and fact_type:
        logger.info(f"Retrying retrieval without fact_type filter for scheme '{scheme_slug}'...")
        chunks = vector_store_manager.search(
            query=query,
            scheme_slug=scheme_slug,
            fact_type=None,
            top_k=top_k,
            score_threshold=0.0
        )
        if chunks and scheme_slug:
            for c in chunks:
                if c["metadata"].get("scheme_slug") == scheme_slug:
                    c["score"] = max(c["score"], 0.85)

    # 3. Global fallback search if no scheme_slug was specified
    if not chunks and not scheme_slug:
        logger.info("Executing global fallback search across all 5 schemes...")
        chunks = vector_store_manager.search(
            query=query,
            scheme_slug=None,
            fact_type=None,
            top_k=top_k,
            score_threshold=0.0
        )

    if not chunks:
        logger.warning(f"No candidate chunks retrieved for query: '{query}'")
        return {
            "retrieved_chunks": [],
            "max_confidence": 0.0,
            "has_context": False
        }

    max_score = max(c["score"] for c in chunks)
    logger.info(f"Retrieved {len(chunks)} candidate chunk(s). Max confidence score: {round(max_score, 3)}")

    return {
        "retrieved_chunks": chunks,
        "max_confidence": max_score,
        "has_context": len(chunks) > 0
    }

if __name__ == "__main__":
    res = retrieve_context("What is the benchmark of HDFC Defence Fund?", scheme_slug="hdfc-defence-fund-direct-growth")
    print("Retrieval result:", res)
