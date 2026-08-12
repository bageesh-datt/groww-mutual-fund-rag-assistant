"""
Groww DOM Parser & Metadata Extractor
Cleans raw HTML snapshots, parses key financial facts (Expense Ratio, Exit Load, Minimum SIP, Benchmark, Riskometer),
and saves structured JSON records for chunking and indexing.
"""

import json
import os
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("ingestion.parser")

class CleanTextExtractor(HTMLParser):
    """HTML Parser that strips script/style tags and collects text tokens."""
    def __init__(self):
        super().__init__()
        self.text_tokens = []
        self.ignore_tag = False

    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style', 'noscript', 'head', 'svg', 'button']:
            self.ignore_tag = True

    def handle_endtag(self, tag):
        if tag in ['script', 'style', 'noscript', 'head', 'svg', 'button']:
            self.ignore_tag = False

    def handle_data(self, data):
        if not self.ignore_tag:
            clean = data.strip()
            if clean:
                self.text_tokens.append(clean)

def extract_text_tokens(html_content: str) -> list[str]:
    parser = CleanTextExtractor()
    parser.feed(html_content)
    return parser.text_tokens

def extract_key_metrics(html_content: str, text_tokens: list[str], slug: str) -> dict[str, str]:
    """
    Extracts key mutual fund metrics using text token windows and regex patterns.
    """
    scheme_info = settings.SCHEME_URL_MAP.get(slug, {})
    scheme_name = scheme_info.get("scheme_name", slug.replace("-", " ").title())

    # Default metrics dictionary
    metrics = {
        "scheme_name": scheme_name,
        "expense_ratio": "N/A",
        "exit_load": "N/A",
        "min_sip_amount": "N/A",
        "min_lumpsum_amount": "N/A",
        "benchmark": "N/A",
        "riskometer": "N/A",
        "nav": "N/A",
        "fund_size_aum": "N/A"
    }

    # 1. Exit Load Extraction
    el_match = re.search(r'Exit load of ([^<\.\n]{5,100}(?:\.|\n|$))', html_content, re.IGNORECASE)
    if el_match:
        raw_el = re.sub(r'<[^>]+>', ' ', f"Exit load of {el_match.group(1).strip()}")
        metrics["exit_load"] = " ".join(raw_el.split())
    else:
        for i, token in enumerate(text_tokens):
            if "exit load" in token.lower() and i + 1 < len(text_tokens):
                snippet = " ".join(text_tokens[i+1:i+6])
                if "1%" in snippet or "redeemed" in snippet.lower() or "nil" in snippet.lower():
                    metrics["exit_load"] = snippet
                    break

    # 2. Benchmark Extraction
    match_bm = re.search(r'"benchmark"\s*:\s*"([^"]+)"', html_content, re.IGNORECASE)
    if match_bm:
        metrics["benchmark"] = match_bm.group(1).strip()
    else:
        bm_match = re.search(r'([A-Z0-9\s\-]+TRI)', html_content)
        if bm_match:
            metrics["benchmark"] = bm_match.group(1).strip()

    # 3. Expense Ratio Extraction
    er_match = re.search(r'Expense ratio\s*([0-9\.]+\s*%)', html_content, re.IGNORECASE)
    if er_match:
        metrics["expense_ratio"] = er_match.group(1).strip()
    else:
        for i, token in enumerate(text_tokens):
            if "expense ratio" in token.lower() and i + 1 < len(text_tokens):
                metrics["expense_ratio"] = text_tokens[i+1]
                break

    # 4. Minimum SIP Amount Extraction
    for i, token in enumerate(text_tokens):
        if "min. for sip" in token.lower() or "min. sip" in token.lower() or "minimum sip" in token.lower():
            if i + 1 < len(text_tokens) and ("₹" in text_tokens[i+1] or text_tokens[i+1].isdigit()):
                metrics["min_sip_amount"] = text_tokens[i+1]
                break

    if metrics["min_sip_amount"] == "N/A":
        sip_match = re.search(r'Min\.\s*for\s*SIP\s*([₹\d,]+)', html_content, re.IGNORECASE)
        if sip_match:
            metrics["min_sip_amount"] = sip_match.group(1).strip()

    # 5. Riskometer Extraction
    for token in text_tokens:
        if token in ["Very High Risk", "Very High", "High Risk", "High", "Moderate Risk", "Moderate", "Low Risk", "Low"]:
            metrics["riskometer"] = token.replace(" Risk", "")
            break

    # 6. NAV Extraction
    nav_match = re.search(r'NAV:[^\n₹]*([₹\d\.]+)', html_content, re.IGNORECASE)
    if nav_match:
        metrics["nav"] = nav_match.group(1).strip()

    # 7. Fund Size / AUM Extraction
    for i, token in enumerate(text_tokens):
        if "fund size" in token.lower() or "aum" in token.lower():
            if i + 1 < len(text_tokens) and "₹" in text_tokens[i+1]:
                metrics["fund_size_aum"] = text_tokens[i+1]
                break

    return metrics

def parse_scheme_html(html_filepath: Path, output_dir: Path = settings.PROCESSED_DATA_DIR) -> dict:
    """
    Parses a single HTML file and produces a structured JSON record.
    """
    slug = html_filepath.stem
    scheme_info = settings.SCHEME_URL_MAP.get(slug, {})
    source_url = scheme_info.get("url", f"https://groww.in/mutual-funds/{slug}")

    logger.info(f"Parsing HTML content for scheme '{slug}'...")

    with open(html_filepath, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    text_tokens = extract_text_tokens(html_content)
    metrics = extract_key_metrics(html_content, text_tokens, slug)

    now_iso = datetime.now().strftime("%d %B %Y")

    record = {
        "scheme_slug": slug,
        "scheme_name": metrics["scheme_name"],
        "source_url": source_url,
        "content_type": "HTML",
        "last_crawled": datetime.now().isoformat(),
        "last_updated_date": now_iso,
        "metrics": metrics,
        "clean_text": "\n".join(text_tokens[:200]),  # Preserved body text blocks
        "fact_snippets": {
            "expense_ratio": f"The expense ratio of {metrics['scheme_name']} is {metrics['expense_ratio']}.",
            "exit_load": f"Exit Load for {metrics['scheme_name']}: {metrics['exit_load']}.",
            "min_sip": f"Minimum SIP amount for {metrics['scheme_name']} is {metrics['min_sip_amount']}.",
            "benchmark": f"The benchmark index of {metrics['scheme_name']} is {metrics['benchmark']}.",
            "riskometer": f"Riskometer rating for {metrics['scheme_name']} is classified as {metrics['riskometer']}."
        }
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_filepath = output_dir / f"{slug}.json"

    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully parsed '{slug}' -> {output_filepath}")
    return record

def parse_all_schemes() -> list[dict]:
    """
    Parses all raw HTML snapshots in data/raw and saves structured JSON records to data/processed.
    """
    logger.info("Starting batch parsing of raw HTML files...")
    raw_files = list(settings.RAW_DATA_DIR.glob("*.html"))

    if not raw_files:
        logger.warning("No raw HTML files found in data/raw/. Running scraper first...")
        from app.ingestion.scraper import fetch_all_schemes
        raw_files = fetch_all_schemes()

    parsed_records = []
    for filepath in raw_files:
        try:
            record = parse_scheme_html(filepath)
            parsed_records.append(record)
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")

    logger.info(f"Batch parsing completed. Processed {len(parsed_records)} record(s).")
    return parsed_records

if __name__ == "__main__":
    parse_all_schemes()
