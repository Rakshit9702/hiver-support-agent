"""Generate transparent, AI-assisted draft labels for human review.

These labels accelerate annotation but must be reviewed before being called a
hand-labelled golden set. Every row keeps the model evidence and review flag.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from hiver_agent import run_agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/apple_support_review_pool.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/apple_support_draft_labels.csv"))
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "tweet_id", "brand", "created_at", "customer_text", "brand_reply",
        "proposed_intent", "proposed_escalated", "proposed_reason", "confidence",
        "evidence", "human_review_status", "human_corrected_intent",
        "human_corrected_escalated", "human_notes",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            prediction = run_agent(row["customer_text"])
            writer.writerow({
                "tweet_id": row["tweet_id"],
                "brand": row["brand"],
                "created_at": row["created_at"],
                "customer_text": row["customer_text"],
                "brand_reply": row["brand_reply"],
                "proposed_intent": prediction.intent,
                "proposed_escalated": prediction.escalated,
                "proposed_reason": prediction.escalation_reason,
                "confidence": prediction.confidence,
                "evidence": "; ".join(prediction.evidence),
                "human_review_status": "PENDING",
                "human_corrected_intent": "",
                "human_corrected_escalated": "",
                "human_notes": "",
            })
    print(f"Wrote {len(rows)} AI-assisted draft labels to {args.output}")


if __name__ == "__main__":
    main()
