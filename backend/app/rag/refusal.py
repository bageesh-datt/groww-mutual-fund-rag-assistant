"""
Deterministic Refusal Engine Module
Generates polite, compliant refusal responses for non-factual queries (Advisory, Performance Prediction, Unsupported Schemes)
with exact citation links and date footers.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag.refusal")

DEFAULT_SCHEME_URL = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"

def get_refusal_url(scheme_slug: str | None) -> str:
    """Returns official scheme URL for citation based on scheme_slug."""
    if scheme_slug and scheme_slug in settings.SCHEME_URL_MAP:
        return settings.SCHEME_URL_MAP[scheme_slug]["url"]
    return DEFAULT_SCHEME_URL

def generate_refusal_response(intent_info: dict) -> dict:
    """
    Generates a compliant refusal response for ADVISORY, PERFORMANCE, or UNSUPPORTED intents.
    """
    intent = intent_info.get("intent", "UNSUPPORTED")
    scheme_slug = intent_info.get("scheme_slug")
    source_url = get_refusal_url(scheme_slug)
    today_date = datetime.now().strftime("%d %B %Y")

    if intent == "ADVISORY":
        answer_text = (
            f"I can provide factual information about supported mutual fund schemes, but I cannot offer "
            f"investment advice, opinions, or fund recommendations. You can review the official scheme page for objective details.\n\n"
            f"Source: [{source_url}]({source_url})\n"
            f"Last updated from sources: {today_date}"
        )
    elif intent == "PERFORMANCE":
        answer_text = (
            f"I cannot predict or calculate expected investment returns. You can review the official scheme page "
            f"for disclosed historical performance information and facts.\n\n"
            f"Source: [{source_url}]({source_url})\n"
            f"Last updated from sources: {today_date}"
        )
    else:  # UNSUPPORTED
        answer_text = (
            f"I can currently provide facts only for the 5 designated Groww mutual fund scheme URLs in my corpus. "
            f"For other schemes or general questions, please consult the official scheme documentation.\n\n"
            f"Source: [{source_url}]({source_url})\n"
            f"Last updated from sources: {today_date}"
        )

    response = {
        "status": "refused",
        "intent": intent,
        "answer": answer_text,
        "source_url": source_url,
        "last_updated": today_date,
        "is_refusal": True
    }

    logger.info(f"Generated refusal response for intent '{intent}' targeting source '{source_url}'")
    return response

if __name__ == "__main__":
    from app.rag.intent import classify_query_intent
    q = "Should I invest in HDFC Small Cap Fund?"
    info = classify_query_intent(q)
    ref = generate_refusal_response(info)
    print("Refusal Output:\n", ref["answer"])
