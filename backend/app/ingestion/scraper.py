"""
Groww Web Scraper Module
Fetches HTML web pages for the 5 designated Groww Mutual Fund scheme URLs.
"""

import os
import sys
import time
import urllib.request
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("ingestion.scraper")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_slug_from_url(url: str) -> str:
    """Extracts scheme slug from URL."""
    return url.rstrip("/").split("/")[-1]

def fetch_scheme_html(url: str, output_dir: Path = settings.RAW_DATA_DIR) -> Path:
    """
    Fetches raw HTML for a single Groww scheme URL and saves it to output_dir.
    """
    if url not in settings.ALLOWED_URLS:
        raise ValueError(f"URL {url} is outside the allowed ingestion scope.")

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = get_slug_from_url(url)
    output_filepath = output_dir / f"{slug}.html"

    logger.info(f"Fetching scheme HTML from: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"Failed to fetch {url}, HTTP status: {response.status}")
            html_content = response.read().decode("utf-8", errors="ignore")

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Successfully saved raw HTML for '{slug}' ({len(html_content)} bytes) -> {output_filepath}")
        return output_filepath

    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        raise

def fetch_all_schemes() -> list[Path]:
    """
    Fetches HTML content for all 5 designated Groww scheme URLs.
    """
    logger.info("Starting batch scrape of all 5 Groww scheme URLs...")
    saved_files = []
    
    for url in settings.ALLOWED_URLS:
        try:
            filepath = fetch_scheme_html(url)
            saved_files.append(filepath)
            time.sleep(1)  # Respectful rate limiting between requests
        except Exception as e:
            logger.error(f"Skipping failed URL {url}: {e}")

    logger.info(f"Batch scrape completed. Saved {len(saved_files)} HTML snapshot(s).")
    return saved_files

if __name__ == "__main__":
    fetch_all_schemes()
