"""
Intent Classifier & Entity Extractor Module
Classifies user queries into FACTUAL, ADVISORY, PERFORMANCE, or UNSUPPORTED intents
and extracts target scheme slugs and fact types.
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

logger = get_logger("rag.intent")

# Keywords for Intent Categories
ADVISORY_PATTERNS = [
    r"\bshould i (?:invest|buy|sell|switch|choose|select)\b",
    r"\bwhich (?:fund|scheme)?\s*is (?:best|better|good|top)\b",
    r"\bwhere (?:should|can) i invest\b",
    r"\brecommend\b",
    r"\bsuggest\b",
    r"\bis it good for\b",
    r"\bportfolio\b",
    r"\badvice\b",
    r"\bopinion\b",
    r"\bbest mutual fund\b",
]

PERFORMANCE_PATTERNS = [
    r"\bhow much will (?:i|my) (?:get|earn|grow)\b",
    r"\bpredict (?:return|returns)\b",
    r"\bexpected (?:return|returns)\b",
    r"\bcalculate (?:return|returns|future)\b",
    r"\bwill (?:i|it) give\b",
    r"\bfuture value\b",
]

UNSUPPORTED_SCHEME_PATTERNS = [
    r"\bsbi\b",
    r"\bicici\b",
    r"\bnippon\b",
    r"\baxis\b",
    r"\bmirae\b",
    r"\bparag parikh\b",
    r"\bquant\b",
    r"\btata\b",
    r"\bkotak\b",
    r"\bdsp\b",
]

FACTUAL_KEYWORDS = [
    "expense ratio", "exit load", "benchmark", "riskometer", "min sip",
    "minimum sip", "lock-in", "nav", "aum", "fund size", "what is", "how much is"
]

# Scheme Mapping Rules
SCHEME_KEYWORD_MAP = {
    "hdfc-mid-cap-fund-direct-growth": ["mid cap", "midcap", "mid-cap"],
    "hdfc-silver-etf-fof-direct-growth": ["silver", "etf fof", "silver fof"],
    "hdfc-defence-fund-direct-growth": ["defence", "defense"],
    "hdfc-equity-fund-direct-growth": ["flexi cap", "flexicap", "equity fund"],
    "hdfc-small-cap-fund-direct-growth": ["small cap", "smallcap", "small-cap"]
}

# Fact Type Mapping
FACT_TYPE_MAP = {
    "expense ratio": "expense_ratio",
    "expense": "expense_ratio",
    "exit load": "exit_load",
    "exit": "exit_load",
    "lock in": "exit_load",
    "lock-in": "exit_load",
    "benchmark": "benchmark",
    "index": "benchmark",
    "riskometer": "riskometer",
    "risk": "riskometer",
    "min sip": "min_sip",
    "minimum sip": "min_sip",
    "sip": "min_sip",
    "nav": "nav_aum",
    "aum": "nav_aum",
    "fund size": "nav_aum"
}

def extract_scheme_slug(query: str) -> str | None:
    """Extracts target scheme slug from query string if present."""
    q_lower = query.lower()
    for slug, keywords in SCHEME_KEYWORD_MAP.items():
        if any(kw in q_lower for kw in keywords):
            return slug
    return None

def extract_fact_type(query: str) -> str | None:
    """Extracts target fact_type from query string if present."""
    q_lower = query.lower()
    for kw, fact_type in FACT_TYPE_MAP.items():
        if kw in q_lower:
            return fact_type
    return None

def classify_query_intent(query: str) -> dict:
    """
    Classifies query intent into FACTUAL, ADVISORY, PERFORMANCE, or UNSUPPORTED.
    Also extracts target scheme_slug and fact_type.
    """
    q_lower = query.strip().lower()

    # 1. Check for Unsupported Schemes (e.g. SBI, ICICI)
    for pattern in UNSUPPORTED_SCHEME_PATTERNS:
        if re.search(pattern, q_lower):
            logger.info(f"Query classified as UNSUPPORTED (unsupported scheme detected in: '{query}')")
            return {
                "intent": "UNSUPPORTED",
                "scheme_slug": None,
                "fact_type": None,
                "reason": "Query asks about a scheme outside the 5 supported Groww scheme URLs."
            }

    # 2. Check for Advisory / Recommendation Intent
    for pattern in ADVISORY_PATTERNS:
        if re.search(pattern, q_lower):
            extracted_slug = extract_scheme_slug(query)
            logger.info(f"Query classified as ADVISORY (advisory pattern matched in: '{query}')")
            return {
                "intent": "ADVISORY",
                "scheme_slug": extracted_slug,
                "fact_type": None,
                "reason": "Query requests investment advice, recommendations, or fund choices."
            }

    # 3. Check for Performance Calculation / Prediction Intent
    for pattern in PERFORMANCE_PATTERNS:
        if re.search(pattern, q_lower):
            extracted_slug = extract_scheme_slug(query)
            logger.info(f"Query classified as PERFORMANCE (performance prediction pattern matched in: '{query}')")
            return {
                "intent": "PERFORMANCE",
                "scheme_slug": extracted_slug,
                "fact_type": None,
                "reason": "Query requests expected return calculations or performance predictions."
            }

    # 4. Check for Factual Intent
    extracted_slug = extract_scheme_slug(query)
    extracted_fact = extract_fact_type(query)

    is_factual = any(kw in q_lower for kw in FACTUAL_KEYWORDS) or (extracted_fact is not None)

    if is_factual:
        logger.info(f"Query classified as FACTUAL (scheme: '{extracted_slug}', fact: '{extracted_fact}')")
        return {
            "intent": "FACTUAL",
            "scheme_slug": extracted_slug,
            "fact_type": extracted_fact,
            "reason": "Query requests objective mutual fund facts."
        }

    # Default to FACTUAL if scheme is identified, else UNSUPPORTED
    if extracted_slug:
        return {
            "intent": "FACTUAL",
            "scheme_slug": extracted_slug,
            "fact_type": extracted_fact,
            "reason": "Scheme identified in query."
        }

    return {
        "intent": "UNSUPPORTED",
        "scheme_slug": None,
        "fact_type": None,
        "reason": "Query does not map to supported factual questions."
    }

if __name__ == "__main__":
    test_queries = [
        "What is the exit load of HDFC Mid-Cap Opportunities Fund Direct Growth?",
        "What is the benchmark of HDFC Defence Fund?",
        "Should I invest in HDFC Small Cap Fund?",
        "Which fund is best for 5 years?",
        "How much will 10k grow in HDFC Silver ETF?",
        "What is the expense ratio of SBI Bluechip Fund?"
    ]
    for q in test_queries:
        print(f"\nQuery: {q}")
        print(" -> Classification:", classify_query_intent(q))
