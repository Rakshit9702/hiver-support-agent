"""Compare agent predictions with the independent reviewer-draft labels."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from hiver_agent import run_agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=Path("data/apple_support_independent_review.csv"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/apple_support/independent_comparison.json"))
    args = parser.parse_args()
    with args.labels.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    intent_correct = routing_correct = 0
    disagreements = []
    for row in rows:
        prediction = run_agent(row["customer_text"])
        expected_escalated = row["independent_escalated"].lower() == "true"
        intent_correct += prediction.intent == row["independent_intent"]
        routing_correct += prediction.escalated == expected_escalated
        if prediction.intent != row["independent_intent"] or prediction.escalated != expected_escalated:
            disagreements.append({"tweet_id": row["tweet_id"], "text": row["customer_text"], "agent_intent": prediction.intent, "reviewer_intent": row["independent_intent"], "agent_escalated": prediction.escalated, "reviewer_escalated": expected_escalated})
    result = {"examples": len(rows), "intent_agreement": round(intent_correct / len(rows), 3), "routing_agreement": round(routing_correct / len(rows), 3), "disagreements": disagreements, "label_status": "independent reviewer draft; audit required"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "disagreements"}, indent=2))

if __name__ == "__main__":
    main()
