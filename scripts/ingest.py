"""
Single CLI Ingestion Script
Runs the end-to-end ingestion pipeline:
1. Web Scraping (5 Groww Scheme URLs)
2. DOM Parsing & Metric Extraction
3. Element-Aware Chunking
4. Dense Vector Database Indexing (BAAI/bge-large-en-v1.5 + ChromaDB)
"""

import sys
import time
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.ingestion.scraper import fetch_all_schemes
from app.ingestion.parser import parse_all_schemes
from app.ingestion.chunker import generate_all_chunks
from app.rag.vector_store import vector_store_manager
from app.utils.logger import get_logger

logger = get_logger("scripts.ingest")

def run_full_ingestion_pipeline():
    start_time = time.time()
    logger.info("==================================================================")
    logger.info("STARTING GROWW MUTUAL FUND FULL INGESTION & INDEXING PIPELINE")
    logger.info("==================================================================")

    # Step 1: Web Scraping
    logger.info("\n--- STEP 1: WEB SCRAPING (5 GROWW SCHEME URLS) ---")
    scraped_files = fetch_all_schemes()
    logger.info(f"Step 1 Complete: {len(scraped_files)} HTML snapshot(s) saved to data/raw/")

    # Step 2: Parsing & Metric Extraction
    logger.info("\n--- STEP 2: DOM PARSING & METRIC EXTRACTION ---")
    parsed_records = parse_all_schemes()
    logger.info(f"Step 2 Complete: {len(parsed_records)} structured record(s) saved to data/processed/")

    # Step 3: Chunking
    logger.info("\n--- STEP 3: ELEMENT-AWARE CHUNKING ---")
    chunks = generate_all_chunks()
    logger.info(f"Step 3 Complete: {len(chunks)} metadata-rich chunk(s) generated.")

    # Step 4: Vector Store Indexing
    logger.info("\n--- STEP 4: VECTOR DB INDEXING (BAAI/bge-large-en-v1.5 + ChromaDB) ---")
    upserted_count = vector_store_manager.upsert_chunks(chunks)
    stats = vector_store_manager.get_stats()
    logger.info(f"Step 4 Complete: {upserted_count} chunk(s) indexed in vector DB.")

    elapsed = round(time.time() - start_time, 2)
    logger.info("==================================================================")
    logger.info(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed} SECONDS")
    logger.info(f"Vector Store Stats: {stats}")
    logger.info("==================================================================")

    return {
        "status": "success",
        "elapsed_seconds": elapsed,
        "scraped_files": len(scraped_files),
        "parsed_records": len(parsed_records),
        "total_chunks": len(chunks),
        "indexed_chunks": upserted_count,
        "vector_store_stats": stats
    }

if __name__ == "__main__":
    run_full_ingestion_pipeline()
