"""Prepare one brand's linked Twitter turns from the Kaggle TWCS dataset.

This creates a review pool, not a golden set: intent and escalation labels must
be hand-checked before evaluation.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

DEFAULT_DATASET = Path.home() / ".cache/kagglehub/datasets/thoughtvector/customer-support-on-twitter/versions/10/twcs/twcs.csv"


def prepare(source: Path, brand: str, output: Path, limit: int) -> int:
    rows: dict[str, dict[str, str]] = {}
    brand_tweets: list[dict[str, str]] = []
    with source.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[row["tweet_id"]] = row
            if row["author_id"] == brand:
                brand_tweets.append(row)

    all_candidates = []
    for reply in brand_tweets:
        parent_id = reply.get("in_response_to_tweet_id")
        parent = rows.get(parent_id or "")
        if not parent or parent["author_id"] == brand or parent["inbound"] != "True":
            continue
        all_candidates.append({
            "tweet_id": parent["tweet_id"],
            "brand": brand,
            "created_at": parent["created_at"],
            "customer_text": parent["text"],
            "brand_reply": reply["text"],
            "brand_reply_tweet_id": reply["tweet_id"],
            "intent": "REVIEW_REQUIRED",
            "escalated": "REVIEW_REQUIRED",
        })
    if len(all_candidates) <= limit:
        candidates = all_candidates
    else:
        indexes = {(index * (len(all_candidates) - 1)) // (limit - 1) for index in range(limit)}
        candidates = [all_candidates[index] for index in sorted(indexes)]

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=candidates[0].keys() if candidates else ["customer_text"])
        writer.writeheader()
        writer.writerows(candidates)
    print(json.dumps({"brand": brand, "linked_examples": len(candidates), "output": str(output)}, indent=2))
    return len(candidates)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--brand", default="AppleSupport")
    parser.add_argument("--output", type=Path, default=Path("data/apple_support_review_pool.csv"))
    parser.add_argument("--limit", type=int, default=250)
    args = parser.parse_args()
    if not args.source.exists():
        raise SystemExit(f"Dataset not found: {args.source}. Run the KaggleHub download first.")
    prepare(args.source, args.brand, args.output, args.limit)


if __name__ == "__main__":
    main()
