"""
Output Validation Guardrail Module
Programmatically evaluates synthesized RAG responses against 5 strict compliance checks:
1. Sentence count <= 3
2. Exactly 1 markdown citation link
3. Citation URL is in settings.ALLOWED_URLS (5 Groww scheme URLs)
4. Presence of "Last updated from sources: <date>" footer
5. Absence of forbidden advisory phrases
"""

import re
import sys
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag.validator")

FORBIDDEN_ADVISORY_PHRASES = [
    "i recommend",
    "you should buy",
    "you should invest",
    "guaranteed return",
    "best fund to buy",
    "switch to this fund",
    "promising returns"
]

def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    """
    Extracts all markdown links [anchor_text](url) from text.
    Returns list of (anchor_text, url) tuples.
    """
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    return re.findall(pattern, text)

def count_answer_sentences(text: str) -> int:
    """
    Counts main narrative sentences in text excluding URLs, Markdown links, and footers.
    """
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        l_str = line.strip()
        if not l_str:
            continue
        if l_str.startswith("Source:") or "Last updated from sources:" in l_str:
            continue
        # Strip Markdown links [text](url) -> text
        clean_line = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'\1', l_str)
        # Strip raw URLs
        clean_line = re.sub(r'https?://[^\s]+', '', clean_line)
        cleaned_lines.append(clean_line)

    body_text = " ".join(cleaned_lines).strip()
    if not body_text:
        return 0

    # Split into sentences
    raw_sentences = re.split(r'(?<=[.!?])\s+', body_text)
    sentences = [s.strip() for s in raw_sentences if s.strip() and len(s.strip()) > 2]
    return len(sentences)

def validate_response(response_text: str, allowed_urls: list[str] = None) -> tuple[bool, str]:
    """
    Validates a generated response against all 5 guardrail checks.
    Returns (True, "OK") if valid, else (False, failure_reason).
    """
    if not allowed_urls:
        allowed_urls = settings.ALLOWED_URLS

    if not response_text or not response_text.strip():
        return False, "Response text is empty."

    # Rule 1: Check Sentence Count (Must be <= 3)
    sentence_count = count_answer_sentences(response_text)
    if sentence_count > settings.MAX_SENTENCES_LIMIT:
        return False, f"Sentence count ({sentence_count}) exceeds limit of {settings.MAX_SENTENCES_LIMIT}."

    # Rule 2: Exactly 1 Markdown Citation Link
    links = extract_markdown_links(response_text)
    if len(links) != settings.REQUIRED_CITATION_COUNT:
        return False, f"Found {len(links)} citation links, required exactly {settings.REQUIRED_CITATION_COUNT}."

    # Rule 3: Citation URL must be in ALLOWED_URLS
    citation_url = links[0][1].strip()
    if citation_url not in allowed_urls:
        return False, f"Citation URL '{citation_url}' is not in the allowed Groww URLs whitelist."

    # Rule 4: Presence of "Last updated from sources:" footer
    if "Last updated from sources:" not in response_text:
        return False, "Missing required footer 'Last updated from sources:'."

    # Rule 5: Zero Advisory Keywords
    text_lower = response_text.lower()
    for phrase in FORBIDDEN_ADVISORY_PHRASES:
        if phrase in text_lower:
            return False, f"Response contains forbidden advisory phrase: '{phrase}'."

    return True, "OK"

def sanitize_or_fallback(response_text: str, allowed_urls: list[str] = None) -> str:
    """
    Validates response_text. If validation fails, replaces it with the safe fallback message.
    """
    is_valid, reason = validate_response(response_text, allowed_urls)
    if is_valid:
        return response_text

    logger.warning(f"Output validation failed ({reason}). Replacing response with safe fallback message.")
    return settings.FALLBACK_RESPONSE_TEXT

if __name__ == "__main__":
    valid_sample = (
        "The expense ratio of HDFC Mid-Cap Opportunities Fund Direct Growth is 0.75%. "
        "The minimum SIP investment is ₹100.\n\n"
        "Source: [Groww Scheme Page](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)\n"
        "Last updated from sources: 12 August 2026"
    )
    print("Valid sample validation:", validate_response(valid_sample))

    invalid_sample_4_sentences = (
        "Sentence one is here. Sentence two is here. Sentence three is here. Sentence four makes it invalid.\n\n"
        "Source: [Groww Scheme Page](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)\n"
        "Last updated from sources: 12 August 2026"
    )
    print("4-sentence validation:", validate_response(invalid_sample_4_sentences))
