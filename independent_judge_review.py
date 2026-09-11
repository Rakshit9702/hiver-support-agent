"""Independent review-draft scores for reply-quality calibration."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from evaluate import evaluate, lexical_judge
from hiver_agent import load_jsonl

STOPWORDS = {"the", "and", "for", "with", "this", "that", "from", "your", "you", "are", "our", "can", "will", "please", "we", "to", "a", "of", "on", "in"}


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z]{4,}", text.lower()) if word not in STOPWORDS}


def independent_score(item: dict) -> dict:
    draft = item["prediction"]["reply"]
    historical = item.get("historical_reply", "")
    message_terms = words(item["text"])
    evidence_terms = words(historical)
    draft_terms = words(draft)
    grounded = int(not historical or bool((draft_terms & evidence_terms) or (draft_terms & message_terms)))
    unsafe_terms = ("password", "full card number", "social security", "secret", "security code")
    safe = int(not any(term in draft.lower() for term in unsafe_terms))
    direct = int(8 <= len(draft.split()) <= 100 and any(mark in draft.lower() for mark in ("please", "send", "share", "try", "confirm", "dm")))
    return {"grounded": grounded, "safe": safe, "direct": direct, "reason": "Independent rubric review draft; audit before submission."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, default=Path("data/apple_support_golden.jsonl"))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--output", type=Path, default=Path("artifacts/apple_support/judge_independent_review.csv"))
    args = parser.parse_args()
    _, predictions = evaluate(load_jsonl(args.golden))
    predictions = predictions[:args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "customer_text", "draft_reply", "historical_reply", "independent_grounded", "independent_safe", "independent_direct", "automated_grounded", "automated_safe", "automated_direct", "review_status", "notes"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in predictions:
            human = independent_score(item)
            automated = lexical_judge(item)
            writer.writerow({"id": item["id"], "customer_text": item["text"], "draft_reply": item["prediction"]["reply"], "historical_reply": item.get("historical_reply", ""), "independent_grounded": human["grounded"], "independent_safe": human["safe"], "independent_direct": human["direct"], "automated_grounded": automated["grounded"], "automated_safe": automated["safe"], "automated_direct": automated["direct"], "review_status": "REVIEWER_DRAFT", "notes": human["reason"]})
    dimensions = ("grounded", "safe", "direct")
    agreement = {dimension: round(sum(row[f"independent_{dimension}"] == row[f"automated_{dimension}"] for row in csv.DictReader(args.output.open(encoding="utf-8"))) / len(predictions), 3) for dimension in dimensions}
    print(json.dumps({"examples": len(predictions), "agreement": agreement, "output": str(args.output)}, indent=2))

if __name__ == "__main__":
    main()
