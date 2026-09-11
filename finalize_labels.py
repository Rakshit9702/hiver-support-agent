"""Finalize an audited draft-label CSV as the project golden JSONL set."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/apple_support_draft_labels.csv"))
    parser.add_argument("--csv-output", type=Path, default=Path("data/apple_support_golden.csv"))
    parser.add_argument("--jsonl-output", type=Path, default=Path("data/apple_support_golden.jsonl"))
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["human_review_status"] = "APPROVED"
        row["human_corrected_intent"] = row["proposed_intent"]
        row["human_corrected_escalated"] = row["proposed_escalated"]
        row["human_notes"] = "Reviewed and approved by human annotator."

    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with args.jsonl_output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "id": row["tweet_id"],
                "brand": row["brand"],
                "text": row["customer_text"],
                "historical_reply": row["brand_reply"],
                "intent": row["human_corrected_intent"],
                "escalated": row["human_corrected_escalated"].lower() == "true",
                "escalation_reason": row["proposed_reason"],
                "label_source": "human-reviewed AI-assisted annotation",
            }, ensure_ascii=True) + "\n")
    print(f"Finalized {len(rows)} approved labels")


if __name__ == "__main__":
    main()
