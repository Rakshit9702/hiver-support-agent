"""Evaluation harness: intent metrics, routing metrics, and optional judge scoring."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from hiver_agent import as_dict, load_jsonl, run_agent, write_jsonl


def evaluate(rows: list[dict]) -> tuple[dict, list[dict]]:
    predictions = []
    intent_correct = routing_correct = 0
    for row in rows:
        prediction = run_agent(row["text"])
        item = {**row, "prediction": as_dict(prediction)}
        predictions.append(item)
        intent_correct += prediction.intent == row["intent"]
        routing_correct += prediction.escalated == row["escalated"]
    confusion = Counter((row["intent"], item["prediction"]["intent"]) for row, item in zip(rows, predictions))
    metrics = {
        "examples": len(rows),
        "intent_accuracy": round(intent_correct / len(rows), 4) if rows else 0,
        "routing_accuracy": round(routing_correct / len(rows), 4) if rows else 0,
        "confusion": {f"{actual}->{predicted}": count for (actual, predicted), count in sorted(confusion.items())},
        "judge": {"protocol": "human rubric required; automated lexical proxy is reported separately", "agreement": None},
    }
    return metrics, predictions


def lexical_judge(item: dict) -> dict:
    """Cheap offline proxy; replace with an LLM judge using the rubric in README."""
    reply = item["prediction"]["reply"].lower()
    grounded = any(word in reply for word in ("please", "send", "share", "try", "confirm"))
    safe = not any(word in reply for word in ("password", "full card", "social security"))
    direct = len(reply) <= 500 and len(reply.split()) >= 8
    return {"grounded": int(grounded), "safe": int(safe), "direct": int(direct), "score": int(grounded) + int(safe) + int(direct)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="data/golden.jsonl")
    parser.add_argument("--out", default="artifacts")
    args = parser.parse_args()
    metrics, predictions = evaluate(load_jsonl(args.golden))
    judged = [lexical_judge(item) for item in predictions]
    metrics["offline_judge_mean"] = round(sum(item["score"] for item in judged) / len(judged), 3) if judged else 0
    output = Path(args.out)
    output.mkdir(exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_jsonl(output / "predictions.jsonl", predictions)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
