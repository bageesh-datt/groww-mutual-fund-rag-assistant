"""
Element-Aware & Semantic Chunker Module
Segments parsed scheme records into atomic key-value metric chunks and paragraph blocks
with rich metadata schemas for vector database indexing.
"""

import json
import sys
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("ingestion.chunker")

def create_chunks_for_record(record: dict) -> list[dict]:
    """
    Creates element-aware metric chunks and clean text paragraph chunks for a scheme record.
    """
    slug = record.get("scheme_slug", "unknown")
    scheme_name = record.get("scheme_name", slug.replace("-", " ").title())
    source_url = record.get("source_url", f"https://groww.in/mutual-funds/{slug}")
    metrics = record.get("metrics", {})
    last_updated = record.get("last_updated_date", "12 August 2026")
    last_crawled = record.get("last_crawled", "")

    chunks = []

    # 1. Expense Ratio Chunk
    er_value = metrics.get("expense_ratio", "N/A")
    if er_value != "N/A":
        chunks.append({
            "chunk_id": f"{slug}_expense_ratio_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "expense_ratio",
            "section_title": "Expense Ratio & Charges",
            "content_format": "key_value",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nFact Category: Expense Ratio\nDetail: The expense ratio of {scheme_name} is {er_value}.\nSource: {source_url}"
        })

    # 2. Exit Load Chunk
    el_value = metrics.get("exit_load", "N/A")
    if el_value != "N/A":
        chunks.append({
            "chunk_id": f"{slug}_exit_load_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "exit_load",
            "section_title": "Exit Load & Redemption Terms",
            "content_format": "key_value",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nFact Category: Exit Load\nDetail: {el_value}\nSource: {source_url}"
        })

    # 3. Minimum SIP Chunk
    sip_value = metrics.get("min_sip_amount", "N/A")
    if sip_value != "N/A":
        chunks.append({
            "chunk_id": f"{slug}_min_sip_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "min_sip",
            "section_title": "Minimum SIP & Investment Limits",
            "content_format": "key_value",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nFact Category: Minimum SIP Amount\nDetail: The minimum SIP investment for {scheme_name} is {sip_value}.\nSource: {source_url}"
        })

    # 4. Benchmark Chunk
    bm_value = metrics.get("benchmark", "N/A")
    if bm_value != "N/A":
        chunks.append({
            "chunk_id": f"{slug}_benchmark_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "benchmark",
            "section_title": "Benchmark Index",
            "content_format": "key_value",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nFact Category: Benchmark Index\nDetail: The benchmark index of {scheme_name} is {bm_value}.\nSource: {source_url}"
        })

    # 5. Riskometer Chunk
    risk_value = metrics.get("riskometer", "N/A")
    if risk_value != "N/A":
        chunks.append({
            "chunk_id": f"{slug}_riskometer_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "riskometer",
            "section_title": "Riskometer Classification",
            "content_format": "key_value",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nFact Category: Riskometer Rating\nDetail: The riskometer rating for {scheme_name} is classified as {risk_value} Risk.\nSource: {source_url}"
        })

    # 6. NAV & Fund Size (AUM) Chunk
    nav_val = metrics.get("nav", "N/A")
    aum_val = metrics.get("fund_size_aum", "N/A")
    if nav_val != "N/A" or aum_val != "N/A":
        chunks.append({
            "chunk_id": f"{slug}_nav_aum_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "nav_aum",
            "section_title": "NAV & Fund Size (AUM)",
            "content_format": "key_value",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nFact Category: NAV & Fund Size\nDetail: Current NAV is ₹{nav_val} and Total Fund Size (AUM) is {aum_val}.\nSource: {source_url}"
        })

    # 7. General Scheme Overview Paragraph Chunk
    clean_text = record.get("clean_text", "")
    if clean_text:
        overview_snippet = clean_text[:600].replace("\n", " ")
        chunks.append({
            "chunk_id": f"{slug}_overview_01",
            "scheme_name": scheme_name,
            "scheme_slug": slug,
            "source_url": source_url,
            "fact_type": "general",
            "section_title": "Scheme Overview",
            "content_format": "paragraph",
            "effective_date": last_updated,
            "last_crawled": last_crawled,
            "text": f"Scheme Name: {scheme_name}\nOverview: {overview_snippet}\nSource: {source_url}"
        })

    return chunks

def generate_all_chunks(processed_dir: Path = settings.PROCESSED_DATA_DIR) -> list[dict]:
    """
    Reads all processed JSON records and generates a unified list of metadata-rich chunks.
    """
    logger.info("Generating semantic & element-aware chunks from processed JSON records...")
    json_files = list(processed_dir.glob("*.json"))

    if not json_files:
        logger.warning("No processed JSON files found. Running parser first...")
        from app.ingestion.parser import parse_all_schemes
        parse_all_schemes()
        json_files = list(processed_dir.glob("*.json"))

    all_chunks = []
    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                record = json.load(f)
            scheme_chunks = create_chunks_for_record(record)
            all_chunks.extend(scheme_chunks)
            logger.info(f"Generated {len(scheme_chunks)} chunk(s) for scheme '{filepath.stem}'")
        except Exception as e:
            logger.error(f"Error chunking {filepath}: {e}")

    logger.info(f"Chunking complete. Total chunks generated across 5 schemes: {len(all_chunks)}")
    return all_chunks

if __name__ == "__main__":
    chunks = generate_all_chunks()
    print(f"Generated {len(chunks)} chunks.")
