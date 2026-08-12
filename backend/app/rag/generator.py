"""
Grounded Answer Generator Module
Synthesizes concise, source-grounded answers from retrieved vector context chunks
and passes responses through the Output Validation Guardrail.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path if running as standalone script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.rag.validator import sanitize_or_fallback, validate_response
from app.utils.logger import get_logger

logger = get_logger("rag.generator")

SYSTEM_PROMPT_TEMPLATE = """You are the Groww Mutual Fund Facts-Only FAQ Assistant.
Your sole job is to provide accurate, concise factual answers about mutual fund schemes based EXCLUSIVELY on the provided context.

STRICT CONSTRAINTS:
1. Answer ONLY using the facts present in the CONTEXT below. Do NOT use outside knowledge or assumptions.
2. If the answer cannot be verified from the CONTEXT, state exactly: "I couldn't verify this information from the available official sources."
3. Your response MUST NOT exceed 3 sentences in total.
4. You MUST include EXACTLY ONE Markdown citation link pointing to the source URL provided in the metadata.
5. You MUST include a footer on a new line: "Last updated from sources: <date>".
6. Do NOT provide investment advice, recommendations, performance predictions, or comparisons.

CONTEXT:
{context_str}

USER QUERY:
{query}
"""

def synthesize_grounded_answer(query: str, retrieved_chunks: list[dict]) -> dict:
    """
    Synthesizes a grounded answer from retrieved vector context chunks.
    """
    if not retrieved_chunks:
        logger.warning("No retrieved context chunks available for generation.")
        return {
            "status": "fallback",
            "answer": settings.FALLBACK_RESPONSE_TEXT,
            "source_url": None,
            "is_valid": False
        }

    # Extract primary metadata from top chunk
    top_chunk = retrieved_chunks[0]
    top_meta = top_chunk.get("metadata", {})
    scheme_name = top_meta.get("scheme_name", "the scheme")
    source_url = top_meta.get("source_url", settings.ALLOWED_URLS[0])
    effective_date = top_meta.get("effective_date", datetime.now().strftime("%d %B %Y"))
    fact_type = top_meta.get("fact_type", "general")

    # Format context string
    context_blocks = []
    for c in retrieved_chunks:
        context_blocks.append(f"Fact Type: {c['metadata'].get('fact_type')}\nContent: {c['text']}")
    context_str = "\n---\n".join(context_blocks)

    raw_answer = ""
    api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY or os.getenv("GROQ_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")

    # 1. Attempt LLM generation if API key is present
    if api_key:
        try:
            import openai
            if api_key.startswith("gsk_"):
                logger.info("Groq API key detected ('gsk_'). Directing request to Groq Cloud endpoint...")
                client = openai.OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                model_name = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")
            else:
                logger.info("OpenAI API key detected. Calling OpenAI API...")
                client = openai.OpenAI(api_key=api_key)
                model_name = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

            prompt = SYSTEM_PROMPT_TEMPLATE.format(context_str=context_str, query=query)
            completion = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150
            )
            raw_answer = completion.choices[0].message.content.strip()
            logger.info("LLM response received successfully.")
        except Exception as e:
            logger.error(f"LLM API generation error: {e}")
            raw_answer = ""

    # 2. High-Precision Deterministic Local Generator Fallback
    if not raw_answer:
        logger.info("Generating grounded answer via local factual synthesizer...")
        # Extract factual statement from chunk text
        chunk_text = top_chunk["text"]
        
        # Clean header/source labels from chunk text if present
        clean_facts = []
        for line in chunk_text.split("\n"):
            if not line.startswith("Scheme Name:") and not line.startswith("Fact Category:") and not line.startswith("Source:"):
                clean_facts.append(line.strip())
        
        main_fact = " ".join(clean_facts).strip() if clean_facts else chunk_text
        
        # Ensure sentence limit
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', main_fact) if s.strip()]
        concise_fact = " ".join(sentences[:2]) if len(sentences) > 2 else main_fact

        raw_answer = (
            f"{concise_fact}\n\n"
            f"Source: [{scheme_name}]({source_url})\n"
            f"Last updated from sources: {effective_date}"
        )

    # 3. Pass raw answer through Output Validation Guardrail
    is_valid, reason = validate_response(raw_answer, allowed_urls=settings.ALLOWED_URLS)
    final_answer = raw_answer if is_valid else settings.FALLBACK_RESPONSE_TEXT

    if not is_valid:
        logger.warning(f"Generated response failed validation guardrail: {reason}")
    else:
        logger.info("Generated response passed all 5 output validation guardrails successfully.")

    return {
        "status": "success" if is_valid else "fallback",
        "answer": final_answer,
        "source_url": source_url,
        "last_updated": effective_date,
        "is_valid": is_valid,
        "validation_reason": reason
    }

if __name__ == "__main__":
    from app.rag.retriever import retrieve_context
    ret = retrieve_context("What is the exit load of HDFC Mid-Cap Opportunities Fund Direct Growth?", scheme_slug="hdfc-mid-cap-fund-direct-growth")
    res = synthesize_grounded_answer("What is the exit load of HDFC Mid-Cap Opportunities Fund Direct Growth?", ret["retrieved_chunks"])
    print("Synthesized Output:\n", res["answer"])
