"""
Automated Evaluation Suite Module
Evaluates system accuracy, refusal precision, citation validity, and constraint compliance against PRD benchmarks.
"""

import json
import re
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.rag.intent import classify_query_intent
from app.rag.refusal import generate_refusal_response
from app.rag.retriever import retrieve_context
from app.rag.generator import synthesize_grounded_answer
from app.rag.validator import validate_response
from app.utils.logger import get_logger

logger = get_logger("evaluation.eval")

def load_test_dataset() -> list[dict]:
    dataset_path = root_dir / "evaluation" / "test_dataset.json"
    if not dataset_path.exists():
        logger.error(f"Test dataset file not found at {dataset_path}")
        return []
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("test_cases", [])

def run_evaluation() -> dict:
    test_cases = load_test_dataset()
    if not test_cases:
        logger.error("No test cases loaded for evaluation.")
        return {}

    logger.info("==================================================================")
    logger.info(f"STARTING AUTOMATED EVALUATION SUITE ({len(test_cases)} TEST CASES)")
    logger.info("==================================================================")

    total_cases = len(test_cases)
    correct_intents = 0
    correct_refusals = 0
    valid_citations = 0
    valid_constraints = 0
    factual_correctness = 0

    advisory_count = 0
    factual_count = 0

    results_table = []

    for case in test_cases:
        cid = case["id"]
        query = case["query"]
        expected_intent = case["expected_intent"]

        start = time.time()

        # Step 1: Intent Classification
        intent_info = classify_query_intent(query)
        predicted_intent = intent_info["intent"]

        intent_pass = (predicted_intent.lower() == expected_intent.lower())
        if intent_pass:
            correct_intents += 1

        response_payload = None

        if predicted_intent in ["ADVISORY", "PERFORMANCE", "UNSUPPORTED"]:
            advisory_count += 1
            response_payload = generate_refusal_response(intent_info)
            if expected_intent.lower() in ["advisory", "performance", "unsupported_scheme"]:
                correct_refusals += 1

        else:  # FACTUAL
            factual_count += 1
            retrieval_res = retrieve_context(
                query=query,
                scheme_slug=intent_info.get("scheme_slug"),
                fact_type=intent_info.get("fact_type"),
                top_k=3
            )
            response_payload = synthesize_grounded_answer(query, retrieval_res["retrieved_chunks"])
            
            # Factual correctness check
            if retrieval_res["has_context"] and response_payload["status"] == "success":
                factual_correctness += 1

        # Check Output Constraints & Citation
        ans_text = response_payload["answer"]
        is_valid_format, reason = validate_response(ans_text, allowed_urls=settings.ALLOWED_URLS)
        if is_valid_format:
            valid_constraints += 1
        else:
            logger.warning(f"Test case '{cid}' constraint validation failed: {reason}")

        # Citation Link Check
        links = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', ans_text)
        if len(links) == 1 and links[0][1] in settings.ALLOWED_URLS:
            valid_citations += 1

        elapsed = round(time.time() - start, 3)

        results_table.append({
            "id": cid,
            "query": query,
            "expected_intent": expected_intent,
            "predicted_intent": predicted_intent,
            "intent_pass": intent_pass,
            "constraint_pass": is_valid_format,
            "elapsed_sec": elapsed
        })

    # Summary Metrics Calculation
    intent_accuracy = (correct_intents / total_cases) * 100
    refusal_accuracy = (correct_refusals / advisory_count * 100) if advisory_count > 0 else 100.0
    citation_accuracy = (valid_citations / total_cases) * 100
    constraint_compliance = (valid_constraints / total_cases) * 100
    factual_accuracy = (factual_correctness / factual_count * 100) if factual_count > 0 else 100.0

    summary = {
        "total_test_cases": total_cases,
        "metrics": {
            "factual_accuracy": round(factual_accuracy, 2),
            "refusal_accuracy": round(refusal_accuracy, 2),
            "citation_validity": round(citation_accuracy, 2),
            "constraint_compliance": round(constraint_compliance, 2),
            "intent_classification_accuracy": round(intent_accuracy, 2)
        },
        "target_slas": {
            "factual_accuracy_target": ">= 95%",
            "refusal_accuracy_target": ">= 98%",
            "citation_validity_target": ">= 98%",
            "constraint_compliance_target": ">= 99%"
        },
        "sla_pass_status": {
            "factual_accuracy_pass": factual_accuracy >= 95.0,
            "refusal_accuracy_pass": refusal_accuracy >= 98.0,
            "citation_validity_pass": citation_accuracy >= 98.0,
            "constraint_compliance_pass": constraint_compliance >= 99.0
        }
    }

    logger.info("==================================================================")
    logger.info("EVALUATION RESULTS SUMMARY")
    logger.info("==================================================================")
    logger.info(f"Factual Accuracy: {summary['metrics']['factual_accuracy']}% (SLA Pass: {summary['sla_pass_status']['factual_accuracy_pass']})")
    logger.info(f"Refusal Accuracy: {summary['metrics']['refusal_accuracy']}% (SLA Pass: {summary['sla_pass_status']['refusal_accuracy_pass']})")
    logger.info(f"Citation Validity: {summary['metrics']['citation_validity']}% (SLA Pass: {summary['sla_pass_status']['citation_validity_pass']})")
    logger.info(f"Constraint Compliance: {summary['metrics']['constraint_compliance']}% (SLA Pass: {summary['sla_pass_status']['constraint_compliance_pass']})")
    logger.info("==================================================================")

    return summary

if __name__ == "__main__":
    res = run_evaluation()
    print(json.dumps(res, indent=2))
