"""Convert the approved independent review CSV into evaluator golden JSONL."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/apple_support_independent_review.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/apple_support_golden_independent.jsonl"))
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "id": row["tweet_id"],
                "brand": "AppleSupport",
                "text": row["customer_text"],
                "historical_reply": row["brand_reply"],
                "intent": row["independent_intent"],
                "escalated": row["independent_escalated"].lower() == "true",
                "escalation_reason": row["independent_reason"],
                "label_source": "independent reviewer pass approved by user",
            }, ensure_ascii=True) + "\n")
    print(f"Wrote {len(rows)} approved independent labels to {args.output}")

if __name__ == "__main__":
    main()
